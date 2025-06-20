# Noteo: Secure NotePad

**Noteo** is a secure, encrypted notepad app with a simple Gradio web interface. Your notes are encrypted with your password and can only be decrypted by you. Notes can be renamed, moved to trash, and permanently deleted after 15 days in the trash.

---

## Features

- **Strong Encryption:** Notes are encrypted using your password and a unique salt.
- **Rename Notes:** Change the title of any note.
- **Trash & Recovery:** Move notes to trash and restore them within 15 days.
- **Auto-Cleanup:** Notes in trash are permanently deleted after 15 days.
- **Simple Web UI:** Powered by Gradio for easy use.

---

## Getting Started

### 1. Clone the Repository

```sh
git clone https://github.com/raviraj4/noteo.git
cd noteo
```

### 2. Install Requirements

Make sure you have Python 3.8+ installed.

```sh
pip install -r requirements.txt
```

### 3. Run the App

```sh
cd frontend
python gradio_ui.py
```
*or*

### 3. create launch the bat file 


The app will open in your browser at `http://localhost:7860`.

---

## Usage

1. **Create a New Note**
   - Enter a new note title in the "New Note Title" box.
   - Click the "New Note" button.

2. **Edit a Note**
   - Select a note from the dropdown.
   - Enter your password.
   - Click "Open" to decrypt and view the note.
   - Edit the content and/or change the title in "Edit Note Title".
   - Click "Save" to update.

3. **Move to Trash**
   - Select a note and click "Move to Trash".
   - Notes in trash can be restored within 15 days.

4. **Restore from Trash**
   - (If implemented in UI) Switch to trash view, select a trashed note, and click "Restore".

5. **Permanent Deletion**
   - Notes in trash are automatically deleted after 15 days.

---

## Security

- **Your notes are encrypted** using your password and a unique salt.
- **Keep your password safe!** Without it, notes cannot be decrypted.
- **Notes are not tracked by git** (see `.gitignore`).

---

## Notes

- The `notes/` directory (with all notes and salts) is ignored by git.
- If you forget your password, your notes cannot be recovered.
- For best security, use a strong, unique password for your notes.

---

## Troubleshooting

- If you see errors about missing files or decryption, make sure you are using the correct password and that the note exists.
- If you have issues, delete the `notes/` directory to reset (this will delete all notes).

---

## License

MIT License

---

**Enjoy secure note