import tkinter as tk
from tkinter import filedialog, messagebox

from core.editor import Editor
from services.file_service import FileService


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Mon Editeur")
        self.geometry("900x600")

        self.editor_core = Editor()
        self.file_service = FileService()

        self.create_widgets()
        self.create_menu()
        self.bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_edit = tk.Text(
            frame,
            wrap=tk.WORD,
            undo=True,
            yscrollcommand=scrollbar.set,
        )
        self.text_edit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_edit.yview)

        self.text_edit.bind("<<Modified>>", self.on_text_changed)

    def create_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=False)
        menu.add_cascade(label="Fichier", menu=file_menu)

        file_menu.add_command(label="Nouveau", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Sauvegarder", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Sauvegarder sous", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.close_window)

    def bind_shortcuts(self):
        self.bind("<Control-n>", lambda _event: self.new_file())
        self.bind("<Control-o>", lambda _event: self.open_file())
        self.bind("<Control-s>", lambda _event: self.save_file())

    def new_file(self):
        if self.confirm_unsaved_changes():
            self.text_edit.delete("1.0", tk.END)
            self.text_edit.edit_modified(False)
            self.editor_core = Editor()
            self.title("Mon Editeur")

    def open_file(self):
        if not self.confirm_unsaved_changes():
            return

        path = filedialog.askopenfilename(title="Ouvrir un fichier")

        if path:
            content = self.file_service.read(path)
            self.editor_core.set_content(content)
            self.editor_core.set_file_path(path)

            self.text_edit.delete("1.0", tk.END)
            self.text_edit.insert("1.0", content)
            self.text_edit.edit_modified(False)
            self.title(f"Mon Editeur - {path}")

    def save_file(self):
        if not self.editor_core.has_file():
            return self.save_file_as()

        content = self.get_text_content()
        success = self.file_service.write(self.editor_core.file_path, content)

        if success:
            self.editor_core.set_content(content)
            self.text_edit.edit_modified(False)

        return success

    def save_file_as(self):
        path = filedialog.asksaveasfilename(title="Sauvegarder sous")

        if not path:
            return False

        content = self.get_text_content()
        success = self.file_service.write(path, content)

        if success:
            self.editor_core.set_file_path(path)
            self.editor_core.set_content(content)
            self.text_edit.edit_modified(False)
            self.title(f"Mon Editeur - {path}")

        return success

    def on_text_changed(self, _event=None):
        if self.text_edit.edit_modified():
            self.editor_core.mark_modified()

    def confirm_unsaved_changes(self) -> bool:
        if not self.editor_core.is_modified():
            return True

        reply = messagebox.askyesnocancel(
            "Modifications non sauvegardees",
            "Voulez-vous sauvegarder avant de continuer ?",
            parent=self,
        )

        if reply is True:
            return bool(self.save_file())

        if reply is False:
            return True

        return False

    def close_window(self):
        if self.confirm_unsaved_changes():
            self.destroy()

    def get_text_content(self) -> str:
        return self.text_edit.get("1.0", "end-1c")
