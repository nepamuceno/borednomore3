import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
import subprocess
import datetime
import json
import webbrowser
import signal
import sys

# Configuración inicial de apariencia
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModernPromptGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Prompt Engine • Ultra Modern")
        self.root.geometry("1280x850")
        self.root.minsize(1000, 750)

        # DEBUG: Initialization started
        print(f"[{datetime.datetime.now()}] Initializing ModernPromptGUI...")

        # Captura de CTRL+C (SIGINT)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.files = [] # Stores dicts: {'path': str, 'enabled': tk.BooleanVar, 'pinned': tk.BooleanVar}
        self.history = [] # Stores dicts: {..., 'pinned': bool, 'id': float}

        # Inclusion Switches Variables
        self.include_rules_var = tk.BooleanVar(value=True)
        self.include_context_var = tk.BooleanVar(value=True)

        # Default Paths
        self.prompt_md_path = "prompt.md"
        self.custom_prompt_default = "custom.md"
        self.state_file = "app_state.json"
        
        # Track current working files for tabs
        self.current_rules_file = self.prompt_md_path
        self.current_custom_file = self.custom_prompt_default

        # AI Engines
        self.ai_engines_path = "ai_engines.json"
        self.ai_engines_data = []
        # List to track entry widgets for the table
        self.engine_rows = [] 
        
        # Carga inicial de datos base si existen
        self.load_initial_content()

        self.create_widgets()
        
        # Seleccionar pestaña Custom Prompt por defecto al iniciar
        self.tabview.set("Custom Prompt")

        # Manejo de cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Cargar estado guardado (incluye archivos de contexto)
        if os.path.exists(self.state_file):
            self.load_state()
        else:
            # Si no hay estado, intentar auto-cargar los archivos por defecto adjuntos
            self.auto_load_default_files()

        # Timer de auto-salvado (5 minutos)
        self.root.after(300000, self.auto_save)
        
        print(f"[{datetime.datetime.now()}] GUI Ready and State Loaded.")

    def load_initial_content(self):
        """Carga contenido inicial de archivos base o los crea si no existen"""
        # Asegurar existencia de archivos mínimos
        for fpath in [self.prompt_md_path, self.custom_prompt_default]:
            if not os.path.exists(fpath):
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("") # Crear vacío

        if os.path.exists(self.prompt_md_path):
            with open(self.prompt_md_path, "r", encoding="utf-8") as f:
                self.prompt_md_content = f.read()

        # Prioridad absoluta a ai_engines.json
        if os.path.exists(self.ai_engines_path):
            try:
                with open(self.ai_engines_path, "r", encoding="utf-8") as f:
                    self.ai_engines_data = json.load(f)
                    print(f"[{datetime.datetime.now()}] Engines loaded from {self.ai_engines_path}")
            except Exception as e:
                print(f"DEBUG: Error loading ai_engines.json: {e}")

    def auto_load_default_files(self):
        """Carga archivos específicos al contexto si no hay estado previo"""
        defaults = [self.ai_engines_path, self.state_file, self.custom_prompt_default, self.prompt_md_path]
        for path in defaults:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path): continue
            if not any(f['path'] == abs_path for f in self.files):
                var = tk.BooleanVar(value=True)
                pin_var = tk.BooleanVar(value=True)
                self.files.append({'path': abs_path, 'enabled': var, 'pinned': pin_var})
        self.refresh_file_list_ui()

    def signal_handler(self, sig, frame):
        """Maneja CTRL+C salvando el estado antes de interrumpir"""
        print(f"\n[{datetime.datetime.now()}] INTERRUPT (Ctrl+C). Saving state...")
        self.save_state()
        sys.exit(0)

    def change_theme(self, new_theme):
        """Cambia el modo de apariencia."""
        ctk.set_appearance_mode(new_theme.lower())
        self.save_state()

    def create_widgets(self):
        # Usamos un Tabview de CustomTkinter
        self.tabview = ctk.CTkTabview(self.root, 
                                     segmented_button_selected_color="#3b8ed0",
                                     segmented_button_unselected_color="#222",
                                     segmented_button_selected_hover_color="#4fa3e0")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_rules = self.tabview.add("✏ Prompt Rules")
        self.tab_custom = self.tabview.add("Custom Prompt")
        self.tab_files = self.tabview.add("Context Files")
        self.tab_ai = self.tabview.add("AI Engines")
        self.tab_history = self.tabview.add("History")

        # --- Tab: Prompt Rules ---
        self.lbl_rules_file = ctk.CTkLabel(self.tab_rules, text=f"Base System Prompt ({self.current_rules_file})", font=("Inter", 14, "bold"), text_color="#3b8ed0")
        self.lbl_rules_file.pack(anchor="w", padx=12, pady=(12,6))
        
        self.prompt_editor = ctk.CTkTextbox(self.tab_rules, font=("JetBrains Mono", 13), border_width=2, border_color="#333", undo=True)
        self.prompt_editor.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.setup_mouse_support(self.prompt_editor)

        btn_rules_frame = ctk.CTkFrame(self.tab_rules, fg_color="transparent")
        btn_rules_frame.pack(fill="x", padx=12, pady=(0,12))
        ctk.CTkButton(btn_rules_frame, text="Save", width=100, fg_color="#2fa572", hover_color="#218c59", command=self.save_prompt_md).pack(side="left", padx=5)
        ctk.CTkButton(btn_rules_frame, text="Save As...", width=100, command=self.save_rules_as).pack(side="left", padx=5)
        ctk.CTkButton(btn_rules_frame, text="Load", width=100, command=self.load_rules_file).pack(side="left", padx=5)
        ctk.CTkButton(btn_rules_frame, text="Clear", width=100, command=lambda: self.prompt_editor.delete("1.0", tk.END)).pack(side="left", padx=5)
        ctk.CTkButton(btn_rules_frame, text="Undo", width=70, fg_color="#444", command=lambda: self.prompt_editor.edit_undo()).pack(side="right", padx=5)
        ctk.CTkButton(btn_rules_frame, text="Redo", width=70, fg_color="#444", command=lambda: self.prompt_editor.edit_redo()).pack(side="right", padx=5)

        # --- Tab: Custom Prompt ---
        self.tab_custom.configure(fg_color="#1e1e1e")
        self.lbl_custom_file = ctk.CTkLabel(self.tab_custom, text=f"Current Task ({self.current_custom_file})", font=("Inter", 14, "bold"), text_color="#2fa572")
        self.lbl_custom_file.pack(anchor="w", padx=12, pady=(12,6))
        
        self.custom_prompt = ctk.CTkTextbox(self.tab_custom, font=("JetBrains Mono", 14), border_width=2, border_color="#2fa572", undo=True, fg_color="#121212")
        self.custom_prompt.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.setup_mouse_support(self.custom_prompt)

        btn_custom_frame = ctk.CTkFrame(self.tab_custom, fg_color="transparent")
        btn_custom_frame.pack(fill="x", padx=12, pady=(0,12))
        ctk.CTkButton(btn_custom_frame, text="Save Task", width=120, fg_color="#2fa572", hover_color="#218c59", font=("Inter", 12, "bold"), command=self.save_custom_prompt).pack(side="left", padx=5)
        ctk.CTkButton(btn_custom_frame, text="Save As...", width=100, command=self.save_custom_as).pack(side="left", padx=5)
        ctk.CTkButton(btn_custom_frame, text="Load", width=100, command=self.load_custom_file).pack(side="left", padx=5)
        ctk.CTkButton(btn_custom_frame, text="Clear", width=100, command=lambda: self.custom_prompt.delete("1.0", tk.END)).pack(side="left", padx=5)
        ctk.CTkButton(btn_custom_frame, text="Undo", width=70, fg_color="#444", command=lambda: self.custom_prompt.edit_undo()).pack(side="right", padx=5)
        ctk.CTkButton(btn_custom_frame, text="Redo", width=70, fg_color="#444", command=lambda: self.custom_prompt.edit_redo()).pack(side="right", padx=5)

        # --- Tab: Context Files ---
        files_header = ctk.CTkFrame(self.tab_files, fg_color="#222")
        files_header.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(files_header, text="INC", font=("Inter", 11, "bold"), width=30).pack(side="left", padx=2)
        ctk.CTkLabel(files_header, text="PIN", font=("Inter", 11, "bold"), width=40).pack(side="left", padx=5)
        ctk.CTkLabel(files_header, text="FILENAME", font=("Inter", 11, "bold"), width=150, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(files_header, text="FULL SYSTEM PATH", font=("Inter", 11, "bold"), anchor="w").pack(side="left", padx=10)

        self.files_scroll = ctk.CTkScrollableFrame(self.tab_files, label_text="")
        self.files_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        btn_files_frame = ctk.CTkFrame(self.tab_files, fg_color="transparent")
        btn_files_frame.pack(fill="x", padx=12, pady=(0,12))
        ctk.CTkButton(btn_files_frame, text="Add File", command=self.add_file).pack(side="left", padx=5)
        ctk.CTkButton(btn_files_frame, text="Clear Unpinned", command=self.clear_files).pack(side="left", padx=5)

        # --- Tab: AI Engines ---
        ai_table_header = ctk.CTkFrame(self.tab_ai, fg_color="#222")
        ai_table_header.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(ai_table_header, text="URL", font=("Inter", 12, "bold"), width=400, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(ai_table_header, text="Description", font=("Inter", 12, "bold"), anchor="w").pack(side="left", padx=35)

        self.ai_scroll = ctk.CTkScrollableFrame(self.tab_ai, label_text="")
        self.ai_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        btn_ai_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        btn_ai_frame.pack(fill="x", padx=12, pady=(0,12))
        ctk.CTkButton(btn_ai_frame, text="Save Engines", width=120, fg_color="#2fa572", command=self.save_ai_engines).pack(side="left", padx=5)
        ctk.CTkButton(btn_ai_frame, text="Save As...", width=100, command=self.save_ai_engines_as).pack(side="left", padx=5)
        ctk.CTkButton(btn_ai_frame, text="Load File", width=100, command=self.load_ai_engines_file).pack(side="left", padx=5)
        ctk.CTkButton(btn_ai_frame, text="Add Row", fg_color="#1f538d", hover_color="darkgreen", width=100, command=self.add_ai_row).pack(side="left", padx=5)
        ctk.CTkButton(btn_ai_frame, text="Clear All", width=100, command=self.clear_ai_engines).pack(side="left", padx=5)
        
        self.refresh_ai_list()

        # --- Tab: History ---
        # NUEVO: Cabecera para identificar campos del historial
        self.setup_history_header()

        self.history_scroll = ctk.CTkScrollableFrame(self.tab_history, label_text="Prompt History Log", label_text_color="#3b8ed0")
        self.history_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        
        btn_hist_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        btn_hist_frame.pack(fill="x", padx=12, pady=(0,12))
        ctk.CTkButton(btn_hist_frame, text="Clear All History", command=self.clear_history).pack(side="left", padx=5)
        ctk.CTkButton(btn_hist_frame, text="Save History As...", command=self.save_history_as).pack(side="left", padx=5)

        # Bottom Action Bar
        self.bottom_frame = ctk.CTkFrame(self.root, height=80, border_width=1, border_color="#444", fg_color="#1a1a1a")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=20)

        self.cb_rules = ctk.CTkCheckBox(self.bottom_frame, text="Include Rules", variable=self.include_rules_var, command=self.save_state)
        self.cb_rules.pack(side="left", padx=10)
        
        self.cb_context = ctk.CTkCheckBox(self.bottom_frame, text="Include Context", variable=self.include_context_var, command=self.save_state)
        self.cb_context.pack(side="left", padx=10)

        ctk.CTkButton(self.bottom_frame, text="🚀 GENERATE PROMPT & COPY TO CLIPBOARD", fg_color="#2fa572", hover_color="#218c59", font=("Inter", 14, "bold"), command=self.generate_prompt).pack(side="left", padx=20)
        
        ctk.CTkButton(self.bottom_frame, text="EXIT", fg_color="#b02a37", hover_color="#8c1c27", width=60, command=self.on_close).pack(side="right", padx=10)

        self.theme_menu = ctk.CTkOptionMenu(self.bottom_frame, values=["Dark", "Light", "System"], width=100, command=self.change_theme)
        self.theme_menu.pack(side="right", padx=10)

        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Ready", font=("Inter", 12), text_color="#aaa")
        self.status_label.pack(side="right", padx=20)

    # NUEVO: Titulos de cabecera para el historial
    def setup_history_header(self):
        header_frame = ctk.CTkFrame(self.tab_history, fg_color="#222", height=30)
        header_frame.pack(fill="x", padx=12, pady=(10, 0))
        
        ctk.CTkLabel(header_frame, text="TYPE", font=("Inter", 10, "bold"), width=35).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="PIN", font=("Inter", 10, "bold"), width=35).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="DATE/TIME", font=("Inter", 10, "bold"), width=120, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="TASK PREVIEW / CONTENT", font=("Inter", 10, "bold"), anchor="w").pack(side="left", padx=20)

    # --- FIXED MOUSE SUPPORT FOR DESKTOP BEHAVIOR ---
    def setup_mouse_support(self, widget):
        """Setup proper desktop mouse behavior with right-click context menu"""
        # Create context menu
        menu = tk.Menu(widget, tearoff=0, bg="#2b2b2b", fg="white", 
                      activebackground="#3b8ed0", borderwidth=0)
        
        # Add menu items with proper callbacks
        menu.add_command(label="Cut", 
                        command=lambda: widget.event_generate("<<Cut>>") if hasattr(widget, 'event_generate') else None)
        menu.add_command(label="Copy", 
                        command=lambda: self.copy_selection(widget))
        menu.add_command(label="Paste", 
                        command=lambda: self.paste_clipboard(widget))
        menu.add_separator()
        menu.add_command(label="Select All", 
                        command=lambda: self.select_all_text(widget))

        def show_menu(event):
            """Show context menu at mouse position"""
            widget.focus_set()
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        # Bind right-click to show menu
        widget.bind("<Button-3>", show_menu)
        
        # Also bind for better selection behavior
        widget.bind("<Button-1>", lambda e: widget.focus_set())

    def copy_selection(self, widget):
        """Copy selected text to clipboard"""
        try:
            if hasattr(widget, 'tag_ranges') and widget.tag_ranges("sel"):
                # Text widget
                selected_text = widget.get("sel.first", "sel.last")
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
            elif hasattr(widget, 'selection_present') and widget.selection_present():
                # Entry widget
                selected_text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
        except:
            pass

    def paste_clipboard(self, widget):
        """Paste from clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                if hasattr(widget, 'insert'):
                    widget.insert("insert", clipboard_text)
                elif hasattr(widget, 'insert'):
                    widget.insert(tk.INSERT, clipboard_text)
        except:
            pass

    def select_all_text(self, widget):
        """Select all text in widget"""
        try:
            if hasattr(widget, 'tag_add'):
                # Text widget
                widget.tag_add("sel", "1.0", "end")
                widget.mark_set("insert", "end")
            elif hasattr(widget, 'select_range'):
                # Entry widget
                widget.select_range(0, tk.END)
                widget.focus_set()
        except:
            pass

    # --- Funcionalidades de Archivos ---

    def add_file(self):
        paths = filedialog.askopenfilenames()
        for path in paths:
            abs_path = os.path.abspath(path)
            if not any(f['path'] == abs_path for f in self.files):
                var = tk.BooleanVar(value=True)
                pin_var = tk.BooleanVar(value=False)
                self.files.append({'path': abs_path, 'enabled': var, 'pinned': pin_var})
        self.refresh_file_list_ui()
        self.save_state()

    def toggle_pin(self, path):
        self.save_state()
        self.refresh_file_list_ui()

    def remove_file(self, path):
        self.files = [f for f in self.files if f['path'] != path]
        self.refresh_file_list_ui()
        self.save_state()

    def refresh_file_list_ui(self):
        for widget in self.files_scroll.winfo_children():
            widget.destroy()
        
        for f_obj in self.files:
            frame = ctk.CTkFrame(self.files_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            ctk.CTkCheckBox(frame, text="", width=20, variable=f_obj['enabled'], command=self.save_state).pack(side="left", padx=2)
            ctk.CTkCheckBox(frame, text="📌", width=40, variable=f_obj['pinned'], command=lambda p=f_obj['path']: self.toggle_pin(p)).pack(side="left", padx=5)
            
            name_color = "#3b8ed0" if f_obj['pinned'].get() else "white"
            ctk.CTkLabel(frame, text=os.path.basename(f_obj['path']), font=("Inter", 12, "bold"), text_color=name_color, width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=f_obj['path'], font=("Inter", 10), text_color="gray").pack(side="left", padx=10)
            
            ctk.CTkButton(frame, text="X", width=30, fg_color="#b02a37", hover_color="#8c1c27", command=lambda p=f_obj['path']: self.remove_file(p)).pack(side="right", padx=5)

    def clear_files(self):
        self.files = [f for f in self.files if f['pinned'].get()]
        self.refresh_file_list_ui()
        self.save_state()

    # --- AI Engines Logic ---

    def refresh_ai_list(self):
        for widget in self.ai_scroll.winfo_children():
            widget.destroy()
        self.engine_rows = []
        for i, engine in enumerate(self.ai_engines_data):
            self.create_ai_row_widgets(engine, i)

    def create_ai_row_widgets(self, data, index):
        frame = ctk.CTkFrame(self.ai_scroll, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        url_entry = ctk.CTkEntry(frame, width=400, font=("JetBrains Mono", 12))
        url_entry.insert(0, data.get('url', ''))
        url_entry.pack(side="left", padx=5)
        self.setup_mouse_support(url_entry)

        desc_entry = ctk.CTkEntry(frame, font=("Inter", 12))
        desc_entry.insert(0, data.get('description', ''))
        desc_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.setup_mouse_support(desc_entry)

        ctk.CTkButton(frame, text="GO", width=40, command=lambda u=url_entry: webbrowser.open(u.get())).pack(side="left", padx=2)
        ctk.CTkButton(frame, text="X", width=30, fg_color="#b02a37", hover_color="#8c1c27", command=lambda idx=index: self.remove_ai_row(idx)).pack(side="left", padx=2)
        
        self.engine_rows.append({'url': url_entry, 'desc': desc_entry, 'frame': frame})

    def add_ai_row(self):
        self.ai_engines_data.append({"url": "", "description": ""})
        self.refresh_ai_list()

    def remove_ai_row(self, index):
        self.sync_engines_from_ui()
        if 0 <= index < len(self.ai_engines_data):
            self.ai_engines_data.pop(index)
        self.refresh_ai_list()
        self.save_state()

    def sync_engines_from_ui(self):
        new_data = []
        for row in self.engine_rows:
            new_data.append({"url": row['url'].get(), "description": row['desc'].get()})
        self.ai_engines_data = new_data

    def save_ai_engines(self):
        self.sync_engines_from_ui()
        with open(self.ai_engines_path, "w", encoding="utf-8") as f:
            json.dump(self.ai_engines_data, f, indent=4)
        self.save_state()
        self.set_status("AI Engines saved to JSON")

    def save_ai_engines_as(self):
        self.sync_engines_from_ui()
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.ai_engines_data, f, indent=4)
            self.set_status(f"Saved to {os.path.basename(path)}")

    def load_ai_engines_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.ai_engines_data = json.load(f)
            self.refresh_ai_list()
            self.save_state()

    def clear_ai_engines(self):
        self.ai_engines_data = []
        self.refresh_ai_list()
        self.save_state()

    # --- Historia Logic ---

    def add_to_history(self, prompt_text):
        entry = {
            'id': datetime.datetime.now().timestamp(),
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rules_used': self.prompt_editor.get("1.0", tk.END).strip(),
            'custom_used': self.custom_prompt.get("1.0", tk.END).strip(),
            'context_files': [f['path'] for f in self.files if f['enabled'].get()],
            'full_content': prompt_text,
            'pinned': False
        }
        self.history.insert(0, entry)
        self.refresh_history_ui()
        self.save_state()

    def toggle_history_pin(self, entry_id):
        for item in self.history:
            if item.get('id') == entry_id:
                item['pinned'] = not item.get('pinned', False)
                break
        self.refresh_history_ui()
        self.save_state()

    def remove_history_item(self, entry_id):
        self.history = [item for item in self.history if item.get('id') != entry_id]
        self.refresh_history_ui()
        self.save_state()

    def clear_history(self):
        self.history = [h for h in self.history if h.get('pinned')]
        self.refresh_history_ui()
        self.save_state()

    def refresh_history_ui(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        
        # Pinned first, then sorted by timestamp
        sorted_history = sorted(self.history, key=lambda x: (not x.get('pinned', False), -x.get('id', 0)))
        
        for entry in sorted_history:
            self.render_history_item(entry)

    def render_history_item(self, entry):
        entry_id = entry.get('id', datetime.datetime.now().timestamp())
        is_pinned = entry.get('pinned', False)
        
        # Feedback visual para items anclados
        bg_color = "#1e3d2f" if is_pinned else "transparent"
        item_frame = ctk.CTkFrame(self.history_scroll, border_width=1, fg_color=bg_color)
        item_frame.pack(fill="x", pady=2, padx=5)
        
        header_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=2)
        
        # TYPE icon
        ctk.CTkLabel(header_frame, text="📜", width=35).pack(side="left", padx=5)
        
        # PIN Button
        pin_text = "📌" if is_pinned else "📍"
        ctk.CTkButton(header_frame, text=pin_text, width=35, height=24, fg_color="transparent", 
                      command=lambda: self.toggle_history_pin(entry_id)).pack(side="left", padx=2)

        # DATE
        ctk.CTkLabel(header_frame, text=entry['time'], font=("Inter", 11), width=120, anchor="w").pack(side="left", padx=10)
        
        # PREVIEW (Alineado con cabecera)
        summary = entry.get('custom_used', "").replace("\n", " ")[:80]
        ctk.CTkLabel(header_frame, text=summary, font=("Inter", 11), text_color="#aaa", anchor="w").pack(side="left", padx=10)
        
        # Botones finales
        ctk.CTkButton(header_frame, text="X", width=30, height=24, fg_color="#b02a37", command=lambda: self.remove_history_item(entry_id)).pack(side="right", padx=5)
        ctk.CTkButton(header_frame, text="Copy", width=60, height=24, command=lambda: self.copy_to_clipboard(entry.get('full_content', ""))).pack(side="right", padx=5)

        # Tree Nodes Container
        tree_container = ctk.CTkFrame(item_frame, fg_color="transparent")
        main_expanded = tk.BooleanVar(value=False)
        
        def toggle_main():
            if main_expanded.get():
                tree_container.pack_forget()
                btn_main_toggle.configure(text="▶")
                main_expanded.set(False)
            else:
                tree_container.pack(fill="x", padx=40, pady=(0, 10))
                btn_main_toggle.configure(text="▼")
                main_expanded.set(True)

        btn_main_toggle = ctk.CTkButton(header_frame, text="▶", width=30, fg_color="transparent", command=toggle_main)
        btn_main_toggle.pack(side="right", padx=5)

        self.create_tree_node(tree_container, "📜 Prompt Rules", entry.get('rules_used', ""))
        self.create_tree_node(tree_container, "✍ Custom Prompt", entry.get('custom_used', ""))
        self.create_tree_node(tree_container, "📁 Context Files", "\n".join(entry.get('context_files', [])) or "No files.")
        self.create_tree_node(tree_container, "🚀 Full Content", entry.get('full_content', ""))

    def create_tree_node(self, parent, label, content):
        node_frame = ctk.CTkFrame(parent, fg_color="transparent")
        node_frame.pack(fill="x", pady=1)
        is_open = tk.BooleanVar(value=False)
        content_box_container = [None] 

        def toggle_node():
            if is_open.get():
                if content_box_container[0]: content_box_container[0].destroy()
                btn_node.configure(text=f"  + {label}")
                is_open.set(False)
            else:
                tb = ctk.CTkTextbox(node_frame, height=150, font=("JetBrains Mono", 11))
                tb.insert("1.0", content)
                tb.configure(state="disabled")
                tb.pack(fill="x", padx=20, pady=5)
                content_box_container[0] = tb
                btn_node.configure(text=f"  - {label}")
                is_open.set(True)
                self.setup_mouse_support(tb)

        btn_node = ctk.CTkButton(node_frame, text=f"  + {label}", anchor="w", fg_color="transparent", 
                                 text_color="#aaa", hover_color="#222", height=24, command=toggle_node)
        btn_node.pack(fill="x")

    # --- Core Logic ---

    def generate_prompt(self):
        parts = []
        
        # 1. Base Rules
        if self.include_rules_var.get():
            rules = self.prompt_editor.get("1.0", tk.END).strip()
            if rules:
                parts.append(rules)
        
        # 2. Custom Prompt (Current Task)
        custom = self.custom_prompt.get("1.0", tk.END).strip()
        if custom:
            parts.append(custom)
        
        # 3. Context Files
        if self.include_context_var.get():
            for f_obj in self.files:
                if f_obj['enabled'].get():
                    fpath = f_obj['path']
                    if os.path.exists(fpath):
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                content = f.read()
                                header = f"\n[Filename: {os.path.basename(fpath)}]\n[Path: {fpath}]"
                                parts.append(header + "\n" + content)
                        except Exception as e:
                            print(f"Error reading {fpath}: {e}")

        final_prompt = "\n\n---\n\n".join(parts)
        
        # Lógica de Prompt Largo
        if len(final_prompt) > 15000:
            if messagebox.askyesno("Prompt Largo", f"El prompt generado es muy grande ({len(final_prompt)} caracteres).\n¿Deseas abrir GitHub Gist para subirlo allí?"):
                webbrowser.open("https://gist.github.com/ ")
                self.copy_to_clipboard(final_prompt)
            else:
                final_prompt = "[Aviso: El prompt es largo y se enviará por partes]\n\n" + final_prompt
                self.copy_to_clipboard(final_prompt)
        else:
            self.copy_to_clipboard(final_prompt)
            
        self.add_to_history(final_prompt)
        self.set_status("✓ Prompt Copied to Clipboard")

    # --- Persistence ---

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def set_status(self, text):
        self.status_label.configure(text=text)
        self.root.after(3000, lambda: self.status_label.configure(text="Ready"))

    def save_state(self, *args):
        self.sync_engines_from_ui() 
        state = {
            'rules_file': self.current_rules_file,
            'custom_file': self.current_custom_file,
            'prompt_md_content': self.prompt_editor.get("1.0", tk.END).strip(),
            'custom_prompt_content': self.custom_prompt.get("1.0", tk.END).strip(),
            'context_files': [
                {'path': f['path'], 'enabled': f['enabled'].get(), 'pinned': f['pinned'].get()} 
                for f in self.files
            ],
            'inc_rules': self.include_rules_var.get(),
            'inc_context': self.include_context_var.get(),
            'history': self.history,
            'ai_engines': self.ai_engines_data
        }
        with open(self.state_file, 'w', encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    def load_state(self):
        if not os.path.exists(self.state_file):
            return
        
        try:
            with open(self.state_file, 'r', encoding="utf-8") as f:
                state = json.load(f)
                
                # Load editor content
                self.prompt_editor.insert("1.0", state.get('prompt_md_content', ''))
                self.custom_prompt.insert("1.0", state.get('custom_prompt_content', ''))
                
                # Load Flags
                self.include_rules_var.set(state.get('inc_rules', True))
                self.include_context_var.set(state.get('inc_context', True))
                
                # Load History
                self.history = state.get('history', [])
                
                # Load Engines
                self.ai_engines_data = state.get('ai_engines', [])
                
                # Load files
                self.files = []
                for f_data in state.get('context_files', []):
                    if os.path.exists(f_data['path']):
                        self.files.append({
                            'path': f_data['path'],
                            'enabled': tk.BooleanVar(value=f_data['enabled']),
                            'pinned': tk.BooleanVar(value=f_data['pinned'])
                        })
                
                self.refresh_file_list_ui()
                self.refresh_history_ui()
                self.refresh_ai_list()
        except Exception as e:
            print(f"Error loading state: {e}")

    def auto_save(self):
        self.save_state()
        self.root.after(300000, self.auto_save)

    def on_close(self):
        self.save_state()
        self.root.destroy()

    # --- File Manager Methods ---

    def save_prompt_md(self):
        content = self.prompt_editor.get("1.0", tk.END).strip()
        with open(self.current_rules_file, "w", encoding="utf-8") as f:
            f.write(content)
        self.set_status(f"Rules saved to {os.path.basename(self.current_rules_file)}")

    def save_rules_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".md", initialfile="prompt.md")
        if path:
            self.current_rules_file = path
            self.save_prompt_md()
            self.lbl_rules_file.configure(text=f"Base System Prompt ({os.path.basename(path)})")

    def load_rules_file(self):
        path = filedialog.askopenfilename(filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
        if path:
            self.current_rules_file = path
            with open(path, "r", encoding="utf-8") as f:
                self.prompt_editor.delete("1.0", tk.END)
                self.prompt_editor.insert("1.0", f.read())
            self.lbl_rules_file.configure(text=f"Base System Prompt ({os.path.basename(path)})")

    def save_custom_prompt(self):
        content = self.custom_prompt.get("1.0", tk.END).strip()
        with open(self.current_custom_file, "w", encoding="utf-8") as f:
            f.write(content)
        self.set_status(f"Task saved to {os.path.basename(self.current_custom_file)}")

    def save_custom_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".md", initialfile="custom.md")
        if path:
            self.current_custom_file = path
            self.save_custom_prompt()
            self.lbl_custom_file.configure(text=f"Current Task ({os.path.basename(path)})")

    def load_custom_file(self):
        path = filedialog.askopenfilename(filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
        if path:
            self.current_custom_file = path
            with open(path, "r", encoding="utf-8") as f:
                self.custom_prompt.delete("1.0", tk.END)
                self.custom_prompt.insert("1.0", f.read())
            self.lbl_custom_file.configure(text=f"Current Task ({os.path.basename(path)})")

    def save_history_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="history_export.json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
            self.set_status("History exported.")

if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernPromptGUI(root)
    root.mainloop()
