import tkinter as tk
from tkinter import filedialog, messagebox

from core.editor import Editor
from services.file_service import FileService


class MainWindow(tk.Tk):
    THEMES = {
        "light": {
            "window_bg": "#f3f3f3",
            "editor_bg": "#ffffff",
            "editor_fg": "#111111",
            "insert_bg": "#111111",
            "select_bg": "#0a64ad",
            "select_fg": "#ffffff",
            "menu_bg": "#f3f3f3",
            "menu_fg": "#111111",
            "active_bg": "#e5e5e5",
            "active_fg": "#111111",
        },
        "dark": {
            "window_bg": "#1f1f1f",
            "editor_bg": "#121212",
            "editor_fg": "#eeeeee",
            "insert_bg": "#eeeeee",
            "select_bg": "#3a78c2",
            "select_fg": "#ffffff",
            "menu_bg": "#2b2b2b",
            "menu_fg": "#eeeeee",
            "active_bg": "#3a3a3a",
            "active_fg": "#ffffff",
        },
    }

    def __init__(self):
        super().__init__()

        self.title("Mon Editeur")
        self.geometry("900x600")

        self.editor_core = Editor()
        self.file_service = FileService()
        self.dark_theme_enabled = tk.BooleanVar(value=False)
        self.menus = []

        self.create_widgets()
        self.create_menu()
        self.apply_theme()
        self.bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_widgets(self):
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.main_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_edit = tk.Text(
            self.main_frame,
            wrap=tk.WORD,
            undo=True,
            yscrollcommand=self.scrollbar.set,
        )
        self.text_edit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_edit.yview)

        self.text_edit.bind("<<Modified>>", self.on_text_changed)

    def create_menu(self):
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Fichier", menu=file_menu)
        self.menus.append(file_menu)

        file_menu.add_command(label="Nouveau", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Sauvegarder", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Sauvegarder sous", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.close_window)

        options_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Options", menu=options_menu)
        self.menus.append(options_menu)

        options_menu.add_checkbutton(
            label="Theme sombre",
            variable=self.dark_theme_enabled,
            command=self.apply_theme,
        )

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

    def apply_theme(self):
        theme_name = "dark" if self.dark_theme_enabled.get() else "light"
        theme = self.THEMES[theme_name]

        self.configure(bg=theme["window_bg"])
        self.main_frame.configure(bg=theme["window_bg"])
        self.scrollbar.configure(
            bg=theme["menu_bg"],
            activebackground=theme["active_bg"],
            troughcolor=theme["window_bg"],
        )
        self.text_edit.configure(
            bg=theme["editor_bg"],
            fg=theme["editor_fg"],
            insertbackground=theme["insert_bg"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"],
        )
        self.menu.configure(
            bg=theme["menu_bg"],
            fg=theme["menu_fg"],
            activebackground=theme["active_bg"],
            activeforeground=theme["active_fg"],
        )

        for menu in self.menus:
            menu.configure(
                bg=theme["menu_bg"],
                fg=theme["menu_fg"],
                activebackground=theme["active_bg"],
                activeforeground=theme["active_fg"],
                selectcolor=theme["editor_bg"],
            )

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
