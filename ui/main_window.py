import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from core.editor import Editor
from services.file_service import FileService


class MainWindow(tk.Tk):
    THEMES = {
        "light": {
            "window_bg": "#eef0f4",
            "surface_bg": "#ffffff",
            "surface_border": "#d7dbe3",
            "toolbar_bg": "#f8f9fb",
            "editor_bg": "#ffffff",
            "editor_fg": "#202124",
            "muted_fg": "#626a78",
            "insert_bg": "#202124",
            "select_bg": "#2f6fed",
            "select_fg": "#ffffff",
            "button_bg": "#ffffff",
            "button_fg": "#202124",
            "button_active_bg": "#e9eefb",
            "menu_bg": "#f8f9fb",
            "menu_fg": "#202124",
            "active_bg": "#e9eefb",
            "active_fg": "#202124",
            "tree_selected_bg": "#dbe7ff",
        },
        "dark": {
            "window_bg": "#181a1f",
            "surface_bg": "#22252c",
            "surface_border": "#333844",
            "toolbar_bg": "#20232a",
            "editor_bg": "#15171c",
            "editor_fg": "#eceff4",
            "muted_fg": "#a4adba",
            "insert_bg": "#eceff4",
            "select_bg": "#4b7bec",
            "select_fg": "#ffffff",
            "button_bg": "#2b3039",
            "button_fg": "#eceff4",
            "button_active_bg": "#384152",
            "menu_bg": "#20232a",
            "menu_fg": "#eceff4",
            "active_bg": "#384152",
            "active_fg": "#ffffff",
            "tree_selected_bg": "#334467",
        },
    }
    TEXT_FILETYPES = (
        ("Fichiers texte", "*.txt"),
        ("Tous les fichiers", "*.*"),
    )

    def __init__(self):
        super().__init__()

        self.title("Mon Editeur")
        self.geometry("980x680")
        self.minsize(720, 480)

        self.editor_core = Editor()
        self.file_service = FileService()
        self.dark_theme_enabled = tk.BooleanVar(value=False)
        self.menus = []
        self.toolbar_buttons = []
        self.syllable_line_counts = []
        self.syllable_count_pending = False
        self.current_folder = None
        self.folder_tree_style_name = "Poetry.Treeview"

        self.create_widgets()
        self.create_menu()
        self.apply_theme()
        self.bind_shortcuts()
        self.update_status()
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_widgets(self):
        self.root_frame = tk.Frame(self, bd=0, highlightthickness=0)
        self.root_frame.pack(fill=tk.BOTH, expand=True)

        self.toolbar = tk.Frame(self.root_frame, bd=0, highlightthickness=0)
        self.toolbar.pack(fill=tk.X, padx=24, pady=(20, 0))

        self.title_block = tk.Frame(self.toolbar, bd=0, highlightthickness=0)
        self.title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.app_title = tk.Label(
            self.title_block,
            text="Poetry Editor",
            anchor="w",
            font=("Segoe UI", 16, "bold"),
        )
        self.app_title.pack(anchor="w")

        self.file_label = tk.Label(
            self.title_block,
            text="Document sans titre",
            anchor="w",
            font=("Segoe UI", 9),
        )
        self.file_label.pack(anchor="w", pady=(2, 0))

        actions = [
            ("Nouveau", self.new_file),
            ("Ouvrir", self.open_file),
            ("Dossier", self.open_folder),
            ("Sauver", self.save_file),
            ("Syllabes", self.show_syllable_count),
        ]
        for label, command in actions:
            button = tk.Button(
                self.toolbar,
                text=label,
                command=command,
                bd=0,
                padx=14,
                pady=8,
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
            )
            button.pack(side=tk.LEFT, padx=(8, 0))
            self.toolbar_buttons.append(button)

        self.workspace = tk.PanedWindow(
            self.root_frame,
            orient=tk.HORIZONTAL,
            bd=0,
            sashwidth=6,
            showhandle=False,
        )
        self.workspace.pack(fill=tk.BOTH, expand=True, padx=24, pady=18)

        self.sidebar_shell = tk.Frame(self.workspace, bd=0, highlightthickness=1)
        self.workspace.add(self.sidebar_shell, minsize=180, width=240)

        self.sidebar_header = tk.Frame(self.sidebar_shell, bd=0, highlightthickness=0)
        self.sidebar_header.pack(fill=tk.X, padx=12, pady=(12, 8))

        self.sidebar_title = tk.Label(
            self.sidebar_header,
            text="Explorateur",
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )
        self.sidebar_title.pack(side=tk.LEFT)

        self.folder_button = tk.Button(
            self.sidebar_header,
            text="Ouvrir",
            command=self.open_folder,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
        )
        self.folder_button.pack(side=tk.RIGHT)
        self.toolbar_buttons.append(self.folder_button)

        self.folder_label = tk.Label(
            self.sidebar_shell,
            text="Aucun dossier ouvert",
            anchor="w",
            font=("Segoe UI", 8),
        )
        self.folder_label.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.tree_frame = tk.Frame(self.sidebar_shell, bd=0, highlightthickness=0)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.folder_tree = ttk.Treeview(
            self.tree_frame,
            columns=("path",),
            displaycolumns=(),
            show="tree",
            selectmode="browse",
            style=self.folder_tree_style_name,
        )
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scrollbar = tk.Scrollbar(self.tree_frame, bd=0, width=12)
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.folder_tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.configure(command=self.folder_tree.yview)
        self.folder_tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.folder_tree.bind("<Double-1>", self.open_selected_tree_file)

        self.editor_shell = tk.Frame(self.workspace, bd=0, highlightthickness=1)
        self.workspace.add(self.editor_shell, minsize=360)

        self.editor_header = tk.Frame(self.editor_shell, bd=0, highlightthickness=0)
        self.editor_header.pack(fill=tk.X, padx=18, pady=(14, 8))

        self.mode_label = tk.Label(
            self.editor_header,
            text="Redaction",
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )
        self.mode_label.pack(side=tk.LEFT)

        self.hint_label = tk.Label(
            self.editor_header,
            text="Ctrl+S pour sauvegarder",
            anchor="e",
            font=("Segoe UI", 9),
        )
        self.hint_label.pack(side=tk.RIGHT)

        self.editor_body = tk.Frame(self.editor_shell, bd=0, highlightthickness=0)
        self.editor_body.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 16))

        self.scrollbar = tk.Scrollbar(self.editor_body, bd=0, width=14)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.syllable_gutter = tk.Canvas(
            self.editor_body,
            width=38,
            bd=0,
            highlightthickness=0,
        )
        self.syllable_gutter.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        self.text_edit = tk.Text(
            self.editor_body,
            wrap=tk.WORD,
            undo=True,
            bd=0,
            padx=20,
            pady=24,
            font=("Georgia", 14),
            spacing1=3,
            spacing2=2,
            spacing3=9,
            yscrollcommand=self.on_text_scroll,
        )
        self.text_edit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.scroll_text)

        self.status_bar = tk.Frame(self.root_frame, bd=0, highlightthickness=0)
        self.status_bar.pack(fill=tk.X, padx=24, pady=(0, 18))

        self.status_left = tk.Label(self.status_bar, anchor="w", font=("Segoe UI", 9))
        self.status_left.pack(side=tk.LEFT)

        self.status_right = tk.Label(self.status_bar, anchor="e", font=("Segoe UI", 9))
        self.status_right.pack(side=tk.RIGHT)

        self.text_edit.bind("<<Modified>>", self.on_text_changed)
        self.text_edit.bind("<KeyRelease>", self.on_editor_navigation)
        self.text_edit.bind("<ButtonRelease>", self.on_editor_navigation)
        self.text_edit.bind("<Configure>", lambda _event: self.schedule_syllable_gutter_redraw())
        self.text_edit.bind("<MouseWheel>", lambda _event: self.schedule_syllable_gutter_redraw(), add="+")

    def create_menu(self):
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Fichier", menu=file_menu)
        self.menus.append(file_menu)

        file_menu.add_command(label="Nouveau", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Ouvrir un dossier", command=self.open_folder, accelerator="Ctrl+K")
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

        tools_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Outils", menu=tools_menu)
        self.menus.append(tools_menu)

        tools_menu.add_command(label="Compter les syllabes", command=self.show_syllable_count)

    def bind_shortcuts(self):
        self.bind("<Control-n>", lambda _event: self.new_file())
        self.bind("<Control-o>", lambda _event: self.open_file())
        self.bind("<Control-s>", lambda _event: self.save_file())
        self.bind("<Control-k>", lambda _event: self.open_folder())

    def new_file(self):
        if self.confirm_unsaved_changes():
            self.text_edit.delete("1.0", tk.END)
            self.text_edit.edit_modified(False)
            self.editor_core = Editor()
            self.clear_syllable_counts()
            self.update_window_title()
            self.update_status()

    def open_file(self):
        if not self.confirm_unsaved_changes():
            return

        path = filedialog.askopenfilename(
            title="Ouvrir un fichier",
            filetypes=self.TEXT_FILETYPES,
        )

        if path:
            self.load_file(path)

    def save_file(self):
        if not self.editor_core.has_file():
            return self.save_file_as()

        content = self.get_text_content()
        success = self.file_service.write(self.editor_core.file_path, content)

        if success:
            self.editor_core.set_content(content)
            self.text_edit.edit_modified(False)
            self.update_window_title()
            self.update_status()
            self.refresh_folder_tree(self.editor_core.file_path)

        return success

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            title="Sauvegarder sous",
            defaultextension=".txt",
            filetypes=self.TEXT_FILETYPES,
        )

        if not path:
            return False

        content = self.get_text_content()
        success = self.file_service.write(path, content)

        if success:
            self.editor_core.set_file_path(path)
            self.editor_core.set_content(content)
            self.text_edit.edit_modified(False)
            self.update_window_title()
            self.update_status()
            self.refresh_folder_tree(path)

        return success

    def open_folder(self):
        path = filedialog.askdirectory(title="Ouvrir un dossier")

        if not path:
            return

        self.current_folder = path
        self.folder_label.configure(text=path)
        self.populate_folder_tree(path)

    def populate_folder_tree(self, path: str):
        self.folder_tree.delete(*self.folder_tree.get_children())
        root_id = self.folder_tree.insert(
            "",
            tk.END,
            text=os.path.basename(path) or path,
            values=(path,),
            open=True,
        )
        self.insert_folder_children(root_id, path)

    def refresh_folder_tree(self, selected_path: str | None = None):
        if not self.current_folder:
            return

        selected_path = selected_path or self.editor_core.file_path

        if selected_path and not self.is_path_in_current_folder(selected_path):
            return

        open_paths = self.get_open_tree_paths()
        self.populate_folder_tree(self.current_folder)

        for path in open_paths:
            item_id = self.find_tree_item_by_path(path)

            if item_id:
                self.ensure_tree_folder_loaded(item_id, path)
                self.folder_tree.item(item_id, open=True)

        if selected_path:
            selected_item = self.find_tree_item_by_path(selected_path)

            if selected_item:
                self.folder_tree.selection_set(selected_item)
                self.folder_tree.focus(selected_item)
                self.folder_tree.see(selected_item)

    def insert_folder_children(self, parent_id: str, path: str):
        try:
            entries = sorted(
                os.scandir(path),
                key=lambda entry: (not entry.is_dir(), entry.name.lower()),
            )
        except OSError:
            return

        for entry in entries:
            if entry.name.startswith("."):
                continue

            label = entry.name
            item_id = self.folder_tree.insert(
                parent_id,
                tk.END,
                text=label,
                values=(entry.path,),
            )

            if entry.is_dir():
                self.folder_tree.insert(item_id, tk.END, text="Chargement...", values=("",))

    def on_tree_open(self, _event=None):
        item_id = self.folder_tree.focus()
        path = self.get_tree_item_path(item_id)

        if not path or not os.path.isdir(path):
            return

        children = self.folder_tree.get_children(item_id)

        if len(children) == 1 and not self.get_tree_item_path(children[0]):
            self.folder_tree.delete(children[0])
            self.insert_folder_children(item_id, path)

    def open_selected_tree_file(self, _event=None):
        item_id = self.folder_tree.focus()
        path = self.get_tree_item_path(item_id)

        if not path or os.path.isdir(path):
            return

        if self.confirm_unsaved_changes():
            self.load_file(path)

    def get_tree_item_path(self, item_id: str) -> str:
        if not item_id:
            return ""

        values = self.folder_tree.item(item_id, "values")
        return values[0] if values else ""

    def get_open_tree_paths(self) -> set[str]:
        open_paths = set()

        def collect_open_paths(parent_id: str):
            for item_id in self.folder_tree.get_children(parent_id):
                path = self.get_tree_item_path(item_id)

                if path and os.path.isdir(path) and self.folder_tree.item(item_id, "open"):
                    open_paths.add(path)
                    collect_open_paths(item_id)

        collect_open_paths("")
        return open_paths

    def ensure_tree_folder_loaded(self, item_id: str, path: str):
        children = self.folder_tree.get_children(item_id)

        if len(children) == 1 and not self.get_tree_item_path(children[0]):
            self.folder_tree.delete(children[0])
            self.insert_folder_children(item_id, path)

    def find_tree_item_by_path(self, target_path: str) -> str:
        root_items = self.folder_tree.get_children("")

        if not root_items or not self.current_folder:
            return ""

        root_id = root_items[0]
        root_path = os.path.abspath(self.current_folder)
        target_path = os.path.abspath(target_path)

        if os.path.normcase(root_path) == os.path.normcase(target_path):
            return root_id

        try:
            relative_path = os.path.relpath(target_path, root_path)
        except ValueError:
            return ""

        if relative_path.startswith(".."):
            return ""

        current_id = root_id
        current_path = root_path

        for part in relative_path.split(os.sep):
            self.ensure_tree_folder_loaded(current_id, current_path)
            next_id = ""

            for child_id in self.folder_tree.get_children(current_id):
                child_path = self.get_tree_item_path(child_id)

                if child_path and os.path.basename(child_path) == part:
                    next_id = child_id
                    current_path = child_path
                    break

            if not next_id:
                return ""

            current_id = next_id

        return current_id

    def is_path_in_current_folder(self, path: str) -> bool:
        if not self.current_folder:
            return False

        try:
            common_path = os.path.commonpath(
                [
                    os.path.abspath(self.current_folder),
                    os.path.abspath(path),
                ]
            )
        except ValueError:
            return False

        return os.path.normcase(common_path) == os.path.normcase(os.path.abspath(self.current_folder))

    def load_file(self, path: str):
        content = self.file_service.read(path)
        self.editor_core.set_content(content)
        self.editor_core.set_file_path(path)

        self.text_edit.delete("1.0", tk.END)
        self.text_edit.insert("1.0", content)
        self.text_edit.edit_modified(False)
        self.clear_syllable_counts()
        self.update_window_title()
        self.update_status()

    def on_text_changed(self, _event=None):
        if self.text_edit.edit_modified():
            self.editor_core.mark_modified()
            self.clear_syllable_counts()
            self.update_window_title()
            self.update_status()
            self.text_edit.edit_modified(False)

    def apply_theme(self):
        theme_name = "dark" if self.dark_theme_enabled.get() else "light"
        theme = self.THEMES[theme_name]

        self.configure(bg=theme["window_bg"])
        self.root_frame.configure(bg=theme["window_bg"])
        self.toolbar.configure(bg=theme["window_bg"])
        self.title_block.configure(bg=theme["window_bg"])
        self.app_title.configure(bg=theme["window_bg"], fg=theme["editor_fg"])
        self.file_label.configure(bg=theme["window_bg"], fg=theme["muted_fg"])
        self.workspace.configure(bg=theme["window_bg"])

        self.sidebar_shell.configure(
            bg=theme["surface_bg"],
            highlightbackground=theme["surface_border"],
            highlightcolor=theme["surface_border"],
        )
        self.sidebar_header.configure(bg=theme["surface_bg"])
        self.sidebar_title.configure(bg=theme["surface_bg"], fg=theme["editor_fg"])
        self.folder_label.configure(bg=theme["surface_bg"], fg=theme["muted_fg"])
        self.tree_frame.configure(bg=theme["surface_bg"])
        self.tree_scrollbar.configure(
            bg=theme["menu_bg"],
            activebackground=theme["active_bg"],
            troughcolor=theme["surface_bg"],
        )

        self.editor_shell.configure(
            bg=theme["surface_bg"],
            highlightbackground=theme["surface_border"],
            highlightcolor=theme["surface_border"],
        )
        self.editor_header.configure(bg=theme["surface_bg"])
        self.mode_label.configure(bg=theme["surface_bg"], fg=theme["editor_fg"])
        self.hint_label.configure(bg=theme["surface_bg"], fg=theme["muted_fg"])
        self.editor_body.configure(bg=theme["surface_bg"])
        self.status_bar.configure(bg=theme["window_bg"])
        self.status_left.configure(bg=theme["window_bg"], fg=theme["muted_fg"])
        self.status_right.configure(bg=theme["window_bg"], fg=theme["muted_fg"])

        self.scrollbar.configure(
            bg=theme["menu_bg"],
            activebackground=theme["active_bg"],
            troughcolor=theme["surface_bg"],
        )
        self.text_edit.configure(
            bg=theme["editor_bg"],
            fg=theme["editor_fg"],
            insertbackground=theme["insert_bg"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"],
        )
        self.syllable_gutter.configure(bg=theme["editor_bg"])
        self.menu.configure(
            bg=theme["menu_bg"],
            fg=theme["menu_fg"],
            activebackground=theme["active_bg"],
            activeforeground=theme["active_fg"],
        )

        ttk.Style(self).configure(
            self.folder_tree_style_name,
            background=theme["surface_bg"],
            foreground=theme["editor_fg"],
            fieldbackground=theme["surface_bg"],
            borderwidth=0,
            rowheight=24,
            font=("Segoe UI", 9),
        )
        ttk.Style(self).map(
            self.folder_tree_style_name,
            background=[("selected", theme["tree_selected_bg"])],
            foreground=[("selected", theme["editor_fg"])],
        )

        for button in self.toolbar_buttons:
            button.configure(
                bg=theme["button_bg"],
                fg=theme["button_fg"],
                activebackground=theme["button_active_bg"],
                activeforeground=theme["button_fg"],
            )

        for menu in self.menus:
            menu.configure(
                bg=theme["menu_bg"],
                fg=theme["menu_fg"],
                activebackground=theme["active_bg"],
                activeforeground=theme["active_fg"],
                selectcolor=theme["editor_bg"],
            )

        self.redraw_syllable_gutter()

    def update_window_title(self):
        marker = "*" if self.editor_core.is_modified() else ""

        if self.editor_core.has_file():
            filename = os.path.basename(self.editor_core.file_path)
            self.title(f"{marker}{filename} - Mon Editeur")
            self.file_label.configure(text=self.editor_core.file_path)
            return

        self.title(f"{marker}Mon Editeur")
        self.file_label.configure(text="Document sans titre")

    def update_status(self):
        content = self.get_text_content()
        words = len(content.split())
        chars = len(content)
        line, column = self.text_edit.index(tk.INSERT).split(".")

        self.status_left.configure(text=f"{words} mots   {chars} caracteres")
        self.status_right.configure(text=f"Ligne {line}, colonne {int(column) + 1}")

    def show_syllable_count(self):
        content = self.get_text_content()
        self.syllable_count_pending = True
        self.syllable_line_counts = []
        self.redraw_syllable_gutter()

        thread = threading.Thread(
            target=self.calculate_syllable_count,
            args=(content,),
            daemon=True,
        )
        thread.start()

    def calculate_syllable_count(self, content: str):
        try:
            line_counts = self.editor_core.count_line_syllables(content)
            total = sum(line_counts)
        except Exception as error:
            error_message = str(error)
            self.after(0, lambda: self.show_syllable_error(error_message))
            return

        self.after(0, lambda: self.display_syllable_count(content, total, line_counts))

    def display_syllable_count(self, content: str, total: int, line_counts: list[int]):
        self.syllable_count_pending = False
        self.syllable_line_counts = line_counts
        self.status_left.configure(text=f"Total: {total} syllabe{'s' if total > 1 else ''}")
        self.redraw_syllable_gutter()

    def show_syllable_error(self, error_message: str):
        self.syllable_count_pending = False
        self.syllable_line_counts = []
        self.redraw_syllable_gutter()
        messagebox.showerror("Syllabes", f"Impossible de compter les syllabes: {error_message}", parent=self)

    def clear_syllable_counts(self):
        self.syllable_count_pending = False
        self.syllable_line_counts = []
        self.redraw_syllable_gutter()

    def on_editor_navigation(self, _event=None):
        self.update_status()
        self.schedule_syllable_gutter_redraw()

    def on_text_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self.schedule_syllable_gutter_redraw()

    def scroll_text(self, *args):
        self.text_edit.yview(*args)
        self.schedule_syllable_gutter_redraw()

    def schedule_syllable_gutter_redraw(self):
        self.after_idle(self.redraw_syllable_gutter)

    def redraw_syllable_gutter(self):
        self.syllable_gutter.delete("all")

        theme_name = "dark" if self.dark_theme_enabled.get() else "light"
        theme = self.THEMES[theme_name]
        fg = theme["muted_fg"]

        if self.syllable_count_pending:
            line_index = self.text_edit.index("@0,0").split(".")[0]
            info = self.text_edit.dlineinfo(f"{line_index}.0")

            if info:
                _x, y, _width, height, _baseline = info
                self.syllable_gutter.create_text(
                    19,
                    y + height // 2,
                    text="...",
                    fill=fg,
                    font=("Segoe UI", 9, "bold"),
                )

            return

        if not self.syllable_line_counts:
            return

        index = self.text_edit.index("@0,0")

        while True:
            line = int(index.split(".")[0])
            info = self.text_edit.dlineinfo(f"{line}.0")

            if info is None:
                break

            if line <= len(self.syllable_line_counts):
                _x, y, _width, height, _baseline = info
                count = self.syllable_line_counts[line - 1]
                text = str(count) if count else ""

                if text:
                    self.syllable_gutter.create_text(
                        19,
                        y + height // 2,
                        text=text,
                        fill=fg,
                        font=("Segoe UI", 9, "bold"),
                    )

            next_index = self.text_edit.index(f"{line + 1}.0")

            if next_index == index:
                break

            index = next_index

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
