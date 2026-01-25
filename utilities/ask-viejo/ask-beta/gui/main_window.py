"""
Prompt Rules Tab - COMPLETE WORKING VERSION
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os

class PromptRulesTab:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        self.create_widgets()
        self.load_prompt_rules()
    
    def create_widgets(self):
        """Create prompt rules widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and buttons
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(title_frame, text="Prompt Rules", font=("Inter", 16, "bold")).pack(side="left")
        
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
    
    def load_prompt_rules(self):
        """Load prompt rules from default file"""
        prompt_file = "prompt.md"
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.insert("1.0", content)
                self.status_label.configure(text=f"Loaded: {prompt_file}")
            except Exception as e:
                self.status_label.configure(text=f"Error loading file: {e}")
    
    def load_from_file(self):
        """Load prompt rules from file"""
        filename = filedialog.askopenfilename(
            parent=self.main_window.root,
            title="Load Prompt Rules",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.insert("1.0", content)
                self.status_label.configure(text=f"Loaded: {os.path.basename(filename)}")
                self.main_window.set_status(f"Loaded prompt rules from {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file: {e}")
    
    def save_to_file(self):
        """Save prompt rules to file"""
        filename = filedialog.asksaveasfilename(
            parent=self.main_window.root,
            title="Save Prompt Rules",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                content = self.text_widget.get("1.0", tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.configure(text=f"Saved: {os.path.basename(filename)}")
                self.main_window.set_status(f"Saved prompt rules to {os.path.basename(filename)}")
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
