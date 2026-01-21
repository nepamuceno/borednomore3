"""
Prompt Rules Tab
Handles the prompt rules tab functionality
"""

import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import os

class PromptRulesTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.current_file = "prompt.md"
        
        self.create_widgets()
        self.load_initial_content()
    
    def create_widgets(self):
        """Create tab widgets"""
        # Header
        self.header_label = ctk.CTkLabel(
            self.parent, 
            text=f"Base System Prompt ({os.path.basename(self.current_file)})", 
            font=("Inter", 14, "bold"), 
            text_color="#3b8ed0"
        )
        self.header_label.pack(anchor="w", padx=12, pady=(12, 6))
        
        # Text editor
        self.text_editor = ctk.CTkTextbox(
            self.parent, 
            font=("JetBrains Mono", 13), 
            border_width=2, 
            border_color="#333", 
            undo=True
        )
        self.text_editor.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Button frame
        button_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        # Buttons
        ctk.CTkButton(
            button_frame, 
            text="Save", 
            width=100, 
            fg_color="#2fa572", 
            hover_color="#218c59", 
            command=self.save_file
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Save As...", 
            width=100, 
            command=self.save_as_file
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Load", 
            width=100, 
            command=self.load_file
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Clear", 
            width=100, 
            command=self.clear_content
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Undo", 
            width=70, 
            fg_color="#444", 
            command=self.undo
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Redo", 
            width=70, 
            fg_color="#444", 
            command=self.redo
        ).pack(side="right", padx=5)
    
    def load_initial_content(self):
        """Load initial content from file"""
        if os.path.exists(self.current_file):
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.insert("1.0", content)
            except Exception as e:
                print(f"Error loading {self.current_file}: {e}")
    
    def get_content(self):
        """Get current content"""
        return self.text_editor.get("1.0", tk.END).strip()
    
    def set_content(self, content):
        """Set content"""
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", content)
    
    def save_file(self):
        """Save current content to file"""
        content = self.get_content()
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.main_app.set_status(f"Rules saved to {os.path.basename(self.current_file)}")
        except Exception as e:
            self.main_app.set_status(f"Error saving file: {e}")
    
    def save_as_file(self):
        """Save content as new file"""
        path = filedialog.asksaveasfilename(
            defaultextension=".md", 
            initialfile="prompt.md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")]
        )
        if path:
            self.current_file = path
            self.save_file()
            self.header_label.configure(text=f"Base System Prompt ({os.path.basename(path)})")
    
    def load_file(self):
        """Load content from file"""
        path = filedialog.askopenfilename(
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.current_file = path
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.set_content(content)
                self.header_label.configure(text=f"Base System Prompt ({os.path.basename(path)})")
                self.main_app.set_status(f"Loaded {os.path.basename(path)}")
            except Exception as e:
                self.main_app.set_status(f"Error loading file: {e}")
    
    def clear_content(self):
        """Clear all content"""
        self.text_editor.delete("1.0", tk.END)
        self.main_app.set_status("Content cleared")
    
    def undo(self):
        """Undo last action"""
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass  # Nothing to undo
    
    def redo(self):
        """Redo last undone action"""
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass  # Nothing to redo
