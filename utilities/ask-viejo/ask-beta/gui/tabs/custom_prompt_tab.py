"""
Custom Prompt Tab - COMPLETE WORKING VERSION
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os

class CustomPromptTab:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        self.create_widgets()
        self.load_custom_prompt()
    
    def create_widgets(self):
        """Create custom prompt widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and buttons
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(title_frame, text="Custom Prompt", font=("Inter", 16, "bold")).pack(side="left")
        
        ctk.CTkButton(title_frame, text="Load from File", command=self.load_from_file).pack(side="right", padx=5)
        ctk.CTkButton(title_frame, text="Save to File", command=self.save_to_file).pack(side="right", padx=5)
        ctk.CTkButton(title_frame, text="Clear", command=self.clear_text).pack(side="right", padx=5)
        
        # Text widget with scrollbar
        text_frame = ctk.CTkFrame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, width=80, height=25, 
                                  bg="#1e1e1e", fg="#ffffff", insertbackground="white",
                                  font=("Inter", 12))
        
        scrollbar = tk.Scrollbar(text_frame, orient="vertical")
        scrollbar.config(command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.text_widget.pack(side="left", fill="both", expand=True)
        
        # Status bar
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", font=("Inter", 10))
        self.status_label.pack(side="bottom", fill="x")
        
        # Bind text changes
        self.text_widget.bind('<KeyRelease>', self.on_text_change)
    
    def load_custom_prompt(self):
        """Load custom prompt from default file"""
        custom_file = "custom.md"
        if os.path.exists(custom_file):
            try:
                with open(custom_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.insert("1.0", content)
                self.status_label.configure(text=f"Loaded: {custom_file}")
            except Exception as e:
                self.status_label.configure(text=f"Error loading file: {e}")
    
    def load_from_file(self):
        """Load custom prompt from file"""
        filename = filedialog.askopenfilename(
            parent=self.main_window.root,
            title="Load Custom Prompt",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.insert("1.0", content)
                self.status_label.configure(text=f"Loaded: {os.path.basename(filename)}")
                self.main_window.set_status(f"Loaded custom prompt from {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file: {e}")
    
    def save_to_file(self):
        """Save custom prompt to file"""
        filename = filedialog.asksaveasfilename(
            parent=self.main_window.root,
            title="Save Custom Prompt",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                content = self.text_widget.get("1.0", tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.configure(text=f"Saved: {os.path.basename(filename)}")
                self.main_window.set_status(f"Saved custom prompt to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")
    
    def clear_text(self):
        """Clear the text widget"""
        self.text_widget.delete("1.0", tk.END)
        self.status_label.configure(text="Text cleared")
    
    def on_text_change(self, event=None):
        """Handle text changes"""
        self.status_label.configure(text="Modified")
        self.main_window.save_state()
