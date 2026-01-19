import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import datetime
import json

class ModernPromptGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Prompt Engine • Modern")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 700)

        self.files = []
        self.history = []

        # Prompt.md - siempre cargamos el archivo real al inicio
        self.prompt_md_path = "prompt.md"
        self.prompt_md = ""
        if os.path.exists(self.prompt_md_path):
            with open(self.prompt_md_path, "r", encoding="utf-8") as f:
                self.prompt_md = f.read().strip()

        # AI Engines - editor único con alineación automática de |
        self.ai_engines_path = "ai_engines.md"
        self.ai_engines_content = ""
        if os.path.exists(self.ai_engines_path):
            with open(self.ai_engines_path, "r", encoding="utf-8") as f:
                self.ai_engines_content = f.read()

        self.custom_prompt_default = "custom_prompt.md"
        self.state_file = "app_state.json"

        self.create_widgets()
        self.bind_shortcuts()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        if os.path.exists(self.state_file):
            self.load_state()

        self.set_theme('dracula')  # Dark theme como default

        self.root.after(300000, self.auto_save)

        self.root.bind("<Control-plus>", lambda e: self.increase_font_size())
        self.root.bind("<Control-minus>", lambda e: self.decrease_font_size())

    def create_widgets(self):
        # Menubar
        self.menubar = tk.Menu(self.root, bg="#1e1e2e", fg="#cdd6f4", 
                               activebackground="#45475a", activeforeground="#f38ba8")
        self.root.config(menu=self.menubar, bg="#1e1e2e")

        theme_menu = tk.Menu(self.menubar, tearoff=0, bg="#1e1e2e", fg="#cdd6f4", 
                             activebackground="#45475a", activeforeground="#f38ba8")
        self.menubar.add_cascade(label="Theme", menu=theme_menu)
        for th in ['Dracula', 'Catppuccin Mocha', 'Nord', 'Rose Pine', 'Tokyo Night']:
            theme_menu.add_command(label=th, command=lambda t=th.lower().replace(' ', '_'): self.set_theme(t))

        # Notebook
        style = ttk.Style()
        style.theme_use('clam')

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0,12))

        # Tab: Prompt Rules
        frame_editor = ttk.Frame(notebook)
        notebook.add(frame_editor, text="✏ Prompt Rules")
        tk.Label(frame_editor, text="Base System Prompt (prompt.md)", font=("Inter", 12, "bold")).pack(anchor="w", padx=12, pady=(12,6))
        self.prompt_editor = tk.Text(frame_editor, wrap="word", undo=True, font=("JetBrains Mono", 12), relief="flat", borderwidth=1)
        self.prompt_editor.insert("1.0", self.prompt_md)
        self.prompt_editor.pack(fill="both", expand=True, padx=12, pady=(0,12))

        btn_frame_editor = ttk.Frame(frame_editor)
        btn_frame_editor.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(btn_frame_editor, text="Save prompt.md", command=self.save_prompt_md, style="Rounded.TButton").pack(side="left", padx=(0,8))
        ttk.Button(btn_frame_editor, text="Undo", command=self.prompt_editor.edit_undo, style="Rounded.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frame_editor, text="Redo", command=self.prompt_editor.edit_redo, style="Rounded.TButton").pack(side="left", padx=4)

        # Tab: Custom Prompt
        frame_custom = ttk.Frame(notebook)
        notebook.add(frame_custom, text="Custom Prompt")
        tk.Label(frame_custom, text="Your custom instructions", font=("Inter", 12, "bold")).pack(anchor="w", padx=12, pady=(12,6))
        self.custom_prompt = tk.Text(frame_custom, wrap="word", undo=True, font=("JetBrains Mono", 12), relief="flat", borderwidth=1)
        self.custom_prompt.pack(fill="both", expand=True, padx=12, pady=(0,12))

        btn_frame_custom = ttk.Frame(frame_custom)
        btn_frame_custom.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(btn_frame_custom, text="Load...", command=self.load_custom_prompt, style="Rounded.TButton").pack(side="left", padx=(0,8))
        ttk.Button(btn_frame_custom, text="Save as custom_prompt.md", command=self.save_custom_prompt, style="Rounded.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frame_custom, text="Undo", command=self.custom_prompt.edit_undo, style="Rounded.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frame_custom, text="Redo", command=self.custom_prompt.edit_redo, style="Rounded.TButton").pack(side="left", padx=4)

        # Tab: Context Files
        frame_files = ttk.Frame(notebook)
        notebook.add(frame_files, text="Context Files")
        self.file_listbox = tk.Listbox(frame_files, font=("Inter", 11), relief="flat", borderwidth=1, activestyle="none")
        self.file_listbox.pack(fill="both", expand=True, padx=12, pady=12)

        btn_frame_files = ttk.Frame(frame_files)
        btn_frame_files.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(btn_frame_files, text="Add File", command=self.add_file, style="Rounded.TButton").pack(side="left", padx=(0,8))
        ttk.Button(btn_frame_files, text="Remove Selected", command=self.remove_file, style="Rounded.TButton").pack(side="left")

        # Tab: AI Engines - editor único con alineación automática de |
        frame_ai = ttk.Frame(notebook)
        notebook.add(frame_ai, text="AI Engines")
        tk.Label(frame_ai, text="List of AI Engines (ai_engines.md) - Formato: URL | Descripción (se alinea automáticamente al guardar)", 
                 font=("Inter", 12, "bold")).pack(anchor="w", padx=12, pady=(12,6))

        self.ai_engines_editor = tk.Text(frame_ai, wrap="none", undo=True, font=("JetBrains Mono", 12), 
                                         relief="flat", borderwidth=1, height=25)
        self.ai_engines_editor.insert("1.0", self.ai_engines_content)
        self.ai_engines_editor.pack(fill="both", expand=True, padx=12, pady=(0,12))

        # Botones
        btn_frame_ai = ttk.Frame(frame_ai)
        btn_frame_ai.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(btn_frame_ai, text="Save ai_engines.md", command=self.save_ai_engines_md, style="Rounded.TButton").pack(side="left", padx=(0,8))
        ttk.Button(btn_frame_ai, text="Undo", command=self.ai_engines_editor.edit_undo, style="Rounded.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frame_ai, text="Redo", command=self.ai_engines_editor.edit_redo, style="Rounded.TButton").pack(side="left", padx=4)

        # Tab: History
        frame_history = ttk.Frame(notebook)
        notebook.add(frame_history, text="History")
        self.history_listbox = tk.Listbox(frame_history, font=("Inter", 11), relief="flat", borderwidth=1, activestyle="none")
        self.history_listbox.pack(fill="both", expand=True, padx=12, pady=12)

        btn_frame_history = ttk.Frame(frame_history)
        btn_frame_history.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(btn_frame_history, text="Load Selected", command=self.reuse_history, style="Rounded.TButton").pack(side="left", padx=(0,8))
        ttk.Button(btn_frame_history, text="Clear History", command=self.clear_history, style="Rounded.TButton").pack(side="left")

        # Bottom Bar
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", pady=10, padx=12)

        ttk.Button(bottom_frame, text="Generate & Copy Prompt", command=self.generate_prompt, style="AccentRounded.TButton").pack(side="left", padx=(0,12))
        ttk.Button(bottom_frame, text="Exit", command=self.exit_program, style="Rounded.TButton").pack(side="left")

        self.status_label = tk.Label(
            bottom_frame,
            text="",
            fg="#f9e2af",
            bg="#2a2a3a",
            font=("Inter", 12, "bold"),
            relief="flat",
            padx=10,
            pady=5
        )
        self.status_label.pack(side="right", padx=10)

        # Temas
        self.themes = {
            'dracula': {
                'bg': '#282a36', 'fg': '#f8f8f2', 'insertbg': '#ff79c6', 'selectbg': '#44475a',
                'button_bg': '#bd93f9', 'button_fg': '#282a36', 'button_active': '#ff79c6',
                'tab_bg': '#21222c', 'tab_selected': '#50fa7b', 'tab_fg': '#f8f8f2'
            },
            'catppuccin_mocha': {
                'bg': '#1e1e2e', 'fg': '#cdd6f4', 'insertbg': '#f5e0dc', 'selectbg': '#45475a',
                'button_bg': '#f38ba8', 'button_fg': '#1e1e2e', 'button_active': '#f5c2e7',
                'tab_bg': '#181825', 'tab_selected': '#fab387', 'tab_fg': '#cdd6f4'
            },
            'nord': {
                'bg': '#2e3440', 'fg': '#d8dee9', 'insertbg': '#88c0d0', 'selectbg': '#434c5e',
                'button_bg': '#5e81ac', 'button_fg': '#eceff4', 'button_active': '#81a1c1',
                'tab_bg': '#3b4252', 'tab_selected': '#88c0d0', 'tab_fg': '#d8dee9'
            },
            'rose_pine': {
                'bg': '#191724', 'fg': '#e0def4', 'insertbg': '#ebbcba', 'selectbg': '#26233a',
                'button_bg': '#eb6f92', 'button_fg': '#191724', 'button_active': '#f6c177',
                'tab_bg': '#1f1d2e', 'tab_selected': '#c4a7e7', 'tab_fg': '#e0def4'
            },
            'tokyo_night': {
                'bg': '#1a1b26', 'fg': '#a9b1d6', 'insertbg': '#7aa2f7', 'selectbg': '#292e42',
                'button_bg': '#7aa2f7', 'button_fg': '#1a1b26', 'button_active': '#bb9af7',
                'tab_bg': '#16161e', 'tab_selected': '#9ece6a', 'tab_fg': '#a9b1d6'
            }
        }

        style.configure("Rounded.TButton", font=("Inter", 11), padding=8, relief="flat", borderwidth=0)
        style.configure("AccentRounded.TButton", font=("Inter", 11, "bold"), padding=10)

    def save_ai_engines_md(self):
        """Guarda el contenido y alinea automáticamente los | con espacios"""
        lines = self.ai_engines_editor.get("1.0", tk.END).strip().splitlines()
        formatted_lines = []

        # Encontrar la longitud máxima de URL para alinear
        max_url_len = 0
        parsed_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '|' in line:
                parts = line.split('|', 1)
                url = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""
                max_url_len = max(max_url_len, len(url))
                parsed_lines.append((url, desc))
            else:
                formatted_lines.append(line)  # Líneas sin | se mantienen igual

        # Reconstruir líneas alineadas
        for url, desc in parsed_lines:
            padding = " " * (max_url_len - len(url) + 4)  # +4 para espacio extra bonito
            formatted_lines.append(f"{url}{padding}| {desc}")

        new_content = "\n".join(formatted_lines) + "\n"
        with open(self.ai_engines_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        self.ai_engines_content = new_content
        self.ai_engines_editor.delete("1.0", tk.END)
        self.ai_engines_editor.insert("1.0", new_content)  # Mostrar versión alineada inmediatamente
        self.set_status("ai_engines.md saved & aligned successfully")

    def set_theme(self, theme_name):
        if theme_name not in self.themes:
            theme_name = 'dracula'

        th = self.themes[theme_name]

        self.root.configure(bg=th['bg'])

        style = ttk.Style()
        style.configure('.', background=th['bg'], foreground=th['fg'], font=("Inter", 11))
        style.configure('TNotebook', background=th['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', background=th['tab_bg'], foreground=th['tab_fg'],
                        padding=[12, 8], font=("Inter", 11))
        style.map('TNotebook.Tab', background=[('selected', th['tab_selected']), ('active', th['button_active'])],
                  foreground=[('selected', 'white'), ('active', 'white')])
        style.configure('TFrame', background=th['bg'])

        style.configure("Rounded.TButton", background=th['button_bg'], foreground=th['button_fg'])
        style.map("Rounded.TButton", background=[('active', th['button_active'])])
        style.configure("AccentRounded.TButton", background=th['button_bg'], foreground=th['button_fg'])
        style.map("AccentRounded.TButton", background=[('active', th['button_active'])])

        for widget in [self.prompt_editor, self.custom_prompt, self.ai_engines_editor]:
            widget.configure(bg=th['bg'], fg=th['fg'], insertbackground=th['insertbg'],
                            selectbackground=th['selectbg'], selectforeground="white",
                            relief="flat", borderwidth=1, highlightthickness=1,
                            highlightbackground=th['button_active'], font=("JetBrains Mono", 12))

        for lb in [self.file_listbox, self.history_listbox]:
            lb.configure(bg=th['bg'], fg=th['fg'], selectbackground=th['selectbg'],
                        selectforeground="white", relief="flat", borderwidth=1,
                        highlightthickness=1, highlightbackground=th['button_active'])

        self.status_label.configure(fg="#f9e2af", bg=th['bg'])

        self.theme = theme_name
        self.set_status(f"Theme: {theme_name.replace('_', ' ').title()} activated")

    def clear_history(self):
        if messagebox.askyesno("Clear History", "¿Seguro que quieres borrar TODO el historial?"):
            self.history = []
            self.history_listbox.delete(0, tk.END)
            self.set_status("Historial borrado")

    def generate_prompt(self):
        base_prompt = self.prompt_editor.get("1.0", tk.END)
        final_prompt = base_prompt + "\n\n" + self.custom_prompt.get("1.0", tk.END)
        for file in self.files:
            with open(file, "r", encoding="utf-8") as f:
                final_prompt += f"\n\n[Filename: {os.path.basename(file)}]\n[Path: {file}]\n{f.read()}"
        self.copy_to_clipboard(final_prompt)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        short_desc = final_prompt.strip().replace('\n', ' ')
        short_desc = (short_desc[:78] + '...') if len(short_desc) > 78 else short_desc

        entry_text = f"{timestamp} • {short_desc}"
        self.history.append((timestamp, final_prompt))
        self.history_listbox.insert(tk.END, entry_text)
        self.set_status("✓ Prompt copied to clipboard")

    def save_prompt_md(self):
        new_content = self.prompt_editor.get("1.0", tk.END)
        with open(self.prompt_md_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        self.set_status("prompt.md saved successfully")

    def save_custom_prompt(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialfile="custom_prompt.md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            text = self.custom_prompt.get("1.0", tk.END).rstrip()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.set_status(f"Saved to: {os.path.basename(file_path)}")

    def load_custom_prompt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            self.custom_prompt.delete("1.0", tk.END)
            self.custom_prompt.insert("1.0", text)

    def add_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.files.append(file_path)
            self.file_listbox.insert(tk.END, file_path)

    def remove_file(self):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.file_listbox.delete(index)
            del self.files[index]

    def reuse_history(self):
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            _, prompt = self.history[index]
            self.custom_prompt.delete("1.0", tk.END)
            self.custom_prompt.insert("1.0", prompt)

    def save_state(self):
        state = {
            'prompt_md': self.prompt_editor.get("1.0", tk.END).strip(),
            'custom_prompt': self.custom_prompt.get("1.0", tk.END).strip(),
            'ai_engines_content': self.ai_engines_editor.get("1.0", tk.END).strip(),
            'files': self.files,
            'history': [(t, p.strip()) for t, p in self.history],
            'theme': self.theme
        }
        with open(self.state_file, 'w', encoding="utf-8") as f:
            json.dump(state, f)

    def load_state(self):
        try:
            with open(self.state_file, 'r', encoding="utf-8") as f:
                state = json.load(f)

            saved_prompt = state.get('prompt_md', '').strip()
            if saved_prompt:
                self.prompt_editor.delete("1.0", tk.END)
                self.prompt_editor.insert("1.0", saved_prompt)

            self.custom_prompt.delete("1.0", tk.END)
            self.custom_prompt.insert("1.0", state.get('custom_prompt', '').strip())

            saved_ai = state.get('ai_engines_content', '').strip()
            if saved_ai:
                self.ai_engines_editor.delete("1.0", tk.END)
                self.ai_engines_editor.insert("1.0", saved_ai)

            self.files = state.get('files', [])
            for file in self.files:
                self.file_listbox.insert(tk.END, file)

            self.history = [(t, p) for t, p in state.get('history', [])]
            for t, _ in self.history:
                self.history_listbox.insert(tk.END, f"{t} • (loaded entry)")

            self.set_theme(state.get('theme', 'dracula'))
        except Exception as e:
            self.set_status(f"Error loading state: {str(e)} → using defaults")

    def on_close(self):
        self.save_state()
        self.root.destroy()

    def exit_program(self):
        if messagebox.askyesno("Exit", "Are you sure you want to quit?"):
            self.on_close()

    def set_status(self, msg):
        self.status_label.config(text=msg)
        self.root.after(8000, lambda: self.status_label.config(text=""))

    def copy_to_clipboard(self, text):
        subprocess.run("xclip -selection clipboard", input=text.encode(), shell=True)

    def bind_shortcuts(self):
        for widget in [self.prompt_editor, self.custom_prompt, self.ai_engines_editor]:
            widget.bind("<Control-a>", lambda e, w=widget: self.select_all(w))
            widget.bind("<Control-c>", lambda e, w=widget: self.copy_selection(w))
            widget.bind("<Control-v>", lambda e, w=widget: self.paste_clipboard(w))

    def select_all(self, widget):
        widget.tag_add("sel", "1.0", "end")
        return "break"

    def copy_selection(self, widget):
        try:
            text = widget.get("sel.first", "sel.last")
            self.copy_to_clipboard(text)
        except tk.TclError:
            pass
        return "break"

    def paste_clipboard(self, widget):
        try:
            text = self.root.clipboard_get()
            widget.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return "break"

    def increase_font_size(self):
        current = self.prompt_editor.cget("font")
        name, size = current.split()[:2]
        new_size = int(size) + 1
        new_font = f"{name} {new_size}"
        for w in [self.prompt_editor, self.custom_prompt, self.ai_engines_editor]:
            w.config(font=new_font)

    def decrease_font_size(self):
        current = self.prompt_editor.cget("font")
        name, size = current.split()[:2]
        new_size = max(8, int(size) - 1)
        new_font = f"{name} {new_size}"
        for w in [self.prompt_editor, self.custom_prompt, self.ai_engines_editor]:
            w.config(font=new_font)

    def auto_save(self):
        self.save_state()
        self.root.after(300000, self.auto_save)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernPromptGUI(root)
    root.mainloop()
