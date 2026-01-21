"""
Context Files Tab - COMPLETE WORKING VERSION
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os

class ContextFilesTab:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.files = []  # List of file dictionaries
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create context files widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and buttons
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(title_frame, text="Context Files", font=("Inter", 16, "bold")).pack(side="left")
        
        ctk.CTkButton(title_frame, text="Add Files", command=self.add_files).pack(side="right", padx=5)
        ctk.CTkButton(title_frame, text="Add Folder", command=self.add_folder).pack(side="right", padx=5)
        
        # Files listbox with scrollbar
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.files_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=20, 
                                       bg="#1e1e1e", fg="#ffffff", selectbackground="#3b8ed0",
                                       font=("Inter", 11))
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.files_listbox.yview)
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.files_listbox.pack(side="left", fill="both", expand=True)
        
        # Bind double-click to toggle enable/disable
        self.files_listbox.bind('<Double-Button-1>', self.toggle_file_enabled)
        
        # Control buttons
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x")
        
        ctk.CTkButton(control_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Refresh", command=self.refresh_list).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Toggle Selected", command=self.toggle_selected).pack(side="left", padx=5)
        
        # Status bar
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", font=("Inter", 10))
        self.status_label.pack(side="bottom", fill="x")
    
    def add_files(self):
        """Add files with proper file dialog"""
        filetypes = [
            ("All files", "*.*"),
            ("Text files", "*.txt"),
            ("Markdown files", "*.md"),
            ("Python files", "*.py"),
            ("JSON files", "*.json"),
            ("YAML files", "*.yaml *.yml")
        ]
        
        files = filedialog.askopenfilenames(
            parent=self.main_window.root,
            title="Select Context Files",
            filetypes=filetypes,
            initialdir=os.path.expanduser("~")
        )
        
        if files:
            added_count = 0
            for file_path in files:
                if os.path.exists(file_path):
                    if self.add_file_to_list(file_path):
                        added_count += 1
            
            self.update_listbox()
            self.status_label.configure(text=f"Added {added_count} files")
            self.main_window.set_status(f"Added {added_count} context files")
    
    def add_folder(self):
        """Add folder with proper directory dialog"""
        folder = filedialog.askdirectory(
            parent=self.main_window.root,
            title="Select Folder to Add Files From",
            initialdir=os.path.expanduser("~")
        )
        
        if folder and os.path.exists(folder):
            added_count = 0
            # Add all files from the selected folder
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.add_file_to_list(file_path):
                        added_count += 1
            
            self.update_listbox()
            self.status_label.configure(text=f"Added {added_count} files from folder")
            self.main_window.set_status(f"Added {added_count} files from folder")
    
    def add_file_to_list(self, file_path):
        """Add a file to the list"""
        # Check if file already exists
        existing_files = [f['path'] for f in self.files]
        if file_path in existing_files:
            return False
        
        # Create file entry
        file_entry = {
            'path': file_path,
            'enabled': tk.BooleanVar(value=True),
            'name': os.path.basename(file_path)
        }
        
        self.files.append(file_entry)
        return True
    
    def update_listbox(self):
        """Update the listbox with current files"""
        self.files_listbox.delete(0, tk.END)
        
        for file_entry in self.files:
            status = "✓" if file_entry['enabled'].get() else "✗"
            display_text = f"{status} {file_entry['name']} ({file_entry['path']})"
            self.files_listbox.insert(tk.END, display_text)
        
        self.main_window.save_state()
    
    def toggle_file_enabled(self, event=None):
        """Toggle enable/disable for double-clicked file"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.files):
                current_value = self.files[index]['enabled'].get()
                self.files[index]['enabled'].set(not current_value)
                self.update_listbox()
    
    def toggle_selected(self):
        """Toggle enable/disable for selected files"""
        selected_indices = self.files_listbox.curselection()
        for index in selected_indices:
            if index < len(self.files):
                current_value = self.files[index]['enabled'].get()
                self.files[index]['enabled'].set(not current_value)
        self.update_listbox()
    
    def remove_selected(self):
        """Remove selected files"""
        selected_indices = self.files_listbox.curselection()
        
        # Remove files in reverse order to maintain indices
        removed_count = 0
        for index in reversed(selected_indices):
            if index < len(self.files):
                del self.files[index]
                removed_count += 1
        
        self.update_listbox()
        self.status_label.configure(text=f"Removed {removed_count} files")
    
    def clear_all(self):
        """Clear all files"""
        count = len(self.files)
        self.files.clear()
        self.update_listbox()
        self.status_label.configure(text=f"Cleared {count} files")
    
    def refresh_list(self):
        """Refresh the file list"""
        self.update_listbox()
        self.status_label.configure(text="List refreshed")
    
    def get_files(self):
        """Get list of enabled files"""
        return [f for f in self.files if f['enabled'].get()]
