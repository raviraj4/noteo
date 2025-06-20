import gradio as gr
import os
import json
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from base64 import urlsafe_b64encode, urlsafe_b64decode
import time
from datetime import datetime, timedelta

# --- Config ---
NOTES_DIR = "notes"
META_FILE = os.path.join(NOTES_DIR, "metadata.json")
TRASH_DIR = os.path.join(NOTES_DIR, "trash")

# --- Setup ---
os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)

def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r") as f:
            return json.load(f)
    return {}

def save_metadata(data):
    with open(META_FILE, "w") as f:
        json.dump(data, f)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt,
        iterations=100_000,
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt(content: str, password: str, salt: bytes) -> bytes:
    key = derive_key(password, salt)
    f = Fernet(key)
    return f.encrypt(content.encode())

def decrypt(token: bytes, password: str, salt: bytes) -> str:
    key = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(token).decode()

def list_notes(include_trashed=False):
    data = load_metadata()
    if include_trashed:
        return list(data.keys())
    return [k for k, v in data.items() if not v.get("trashed")]

def create_note(title):
    data = load_metadata()
    if title in data:
        return gr.update(value="Title already exists!", visible=True), gr.update()
    # Generate a unique salt for this note
    salt = secrets.token_bytes(16)
    filename = f"{title}.enc"
    saltfile = f"{title}.salt"
    data[title] = {"file": filename, "salt": saltfile}
    save_metadata(data)
    with open(os.path.join(NOTES_DIR, saltfile), "wb") as f:
        f.write(salt)
    return gr.update(value="New note created.", visible=True), gr.update(choices=list_notes(), value=title)

def save_note(title, new_title, content, password):
    data = load_metadata()
    meta = data.get(title)
    if not meta:
        return "Note not found.", gr.update(choices=list_notes(), value=title)
    saltfile = os.path.join(NOTES_DIR, meta["salt"])
    if not os.path.exists(saltfile):
        return "Salt file missing.", gr.update(choices=list_notes(), value=title)
    salt = open(saltfile, "rb").read()
    encrypted = encrypt(content, password, salt)

    # Handle renaming
    if new_title and new_title != title:
        if new_title in data:
            return "New title already exists.", gr.update(choices=list_notes(), value=title)
        # Rename files
        new_encfile = f"{new_title}.enc"
        new_saltfile = f"{new_title}.salt"
        os.rename(os.path.join(NOTES_DIR, meta["file"]), os.path.join(NOTES_DIR, new_encfile))
        os.rename(saltfile, os.path.join(NOTES_DIR, new_saltfile))
        # Update metadata
        data[new_title] = {"file": new_encfile, "salt": new_saltfile}
        del data[title]
        save_metadata(data)
        meta = data[new_title]
        title = new_title  # Update for saving below

    # Save encrypted content
    with open(os.path.join(NOTES_DIR, meta["file"]), "wb") as f:
        f.write(encrypted)
    save_metadata(data)
    return "Note saved successfully.", gr.update(choices=list_notes(), value=title)

def open_note(title, password):
    data = load_metadata()
    meta = data.get(title)
    if not meta:
        return "Note not found.", ""
    saltfile = os.path.join(NOTES_DIR, meta["salt"])
    if not os.path.exists(saltfile):
        return "Salt file missing.", ""
    salt = open(saltfile, "rb").read()
    encfile = os.path.join(NOTES_DIR, meta["file"])
    if not os.path.exists(encfile):
        return "Encrypted note file missing.", ""
    try:
        with open(encfile, "rb") as f:
            encrypted = f.read()
        decrypted = decrypt(encrypted, password, salt)
        return "Note decrypted.", decrypted
    except Exception as e:
        return f"Error: {str(e)}", ""

def move_to_trash(title):
    data = load_metadata()
    meta = data.get(title)
    if not meta:
        return "Note not found.", gr.update(choices=list_notes(), value=None)
    # Move files to trash
    for key in ["file", "salt"]:
        src = os.path.join(NOTES_DIR, meta[key])
        dst = os.path.join(TRASH_DIR, meta[key])
        if os.path.exists(src):
            os.rename(src, dst)
    # Mark as trashed
    meta["trashed"] = True
    meta["trashed_at"] = time.time()
    save_metadata(data)
    return "Note moved to trash.", gr.update(choices=list_notes(), value=None)

def list_trashed_notes():
    data = load_metadata()
    return [k for k, v in data.items() if v.get("trashed")]

def restore_note(title):
    data = load_metadata()
    meta = data.get(title)
    if not meta or not meta.get("trashed"):
        return "Note not in trash.", gr.update(choices=list_trashed_notes(), value=None)
    # Move files back from trash
    for key in ["file", "salt"]:
        src = os.path.join(TRASH_DIR, meta[key])
        dst = os.path.join(NOTES_DIR, meta[key])
        if os.path.exists(src):
            os.rename(src, dst)
    meta["trashed"] = False
    meta.pop("trashed_at", None)
    save_metadata(data)
    return "Note restored.", gr.update(choices=list_trashed_notes(), value=None)

def cleanup_trash():
    data = load_metadata()
    now = time.time()
    to_delete = []
    for title, meta in data.items():
        if meta.get("trashed") and now - meta.get("trashed_at", now) > 15 * 24 * 3600:
            # Delete files
            for key in ["file", "salt"]:
                f = os.path.join(TRASH_DIR, meta[key])
                if os.path.exists(f):
                    os.remove(f)
            to_delete.append(title)
    for title in to_delete:
        del data[title]
    if to_delete:
        save_metadata(data)

# Call cleanup_trash() at app start
cleanup_trash()

# --- Gradio UI ---
with gr.Blocks(title="Secure NotePad") as demo:
    gr.Markdown("## 🔐 Noteo: Secure NotePad")

    with gr.Row():
        note_list = gr.Dropdown(
            label="Select Note", 
            choices=list_notes(), 
            value=None, 
            info="Choose a note to open or edit"
        )
        new_title = gr.Textbox(
            placeholder="New note title", 
            label="New Note Title", 
            info="Enter a title to create a new note"
        )
        edit_title = gr.Textbox(
            placeholder="Edit selected note title", 
            label="Edit Note Title", 
            info="Change the title of the selected note"
        )
        create_btn = gr.Button(
            "New Note", 
            scale=0.5, 
            size="sm", 
            variant="secondary"
        )

    password = gr.Textbox(
        label="Password (for encryption/decryption)", 
        type="password", 
        placeholder="Enter your password"
    )
    note_area = gr.Textbox(
        label="Note Content", 
        lines=20, 
        placeholder="Type your note here..."
    )
    
    with gr.Row():
        save_btn = gr.Button("Save", variant="primary")
        open_btn = gr.Button("Open")
        move_trash_btn = gr.Button("Move to Trash", variant="stop")

    status = gr.Textbox(
        label="Status", 
        interactive=False, 
        visible=False, 
        show_copy_button=False
    )

    # --- Button Logic ---
    create_btn.click(create_note, [new_title], [status, note_list])
    save_btn.click(save_note, [note_list, edit_title, note_area, password], [status, note_list])
    open_btn.click(open_note, [note_list, password], [status, note_area])
    move_trash_btn.click(move_to_trash, [note_list], [status, note_list])

demo.launch()
