"""
History Tab - COMPLETE WORKING VERSION
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import json
import os
import datetime

class HistoryTab:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.history_file = "history.json"
        self.history_data = []
        
        self.create_widgets()
        self.load_history()
    
    def create_widgets(self):
        """Create history widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and buttons
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(title_frame, text="Prompt History", font=("Inter", 16, "bold")).pack(side="left")
        
        ctk.CTkButton(title_frame, text="Clear History", command=self.clear_history).pack(side="right", padx=5)
        ctk.CTkButton(title_frame, text="Refresh", command=self.refresh_history).pack(side="right", padx=5)
        ctk.CTkButton(title_frame, text="Export History", command=self.export_history).pack(side="right", padx=5)
        
        # History listbox with scrollbar
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.history_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=25, 
                                         bg="#1e1e1e", fg="#ffffff", selectbackground="#3b8ed0",
                                         font=("Inter", 11))
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.history_listbox.yview)
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.history_listbox.pack(side="left", fill="both", expand=True)
        
        # Bind double-click to copy
        self.history_listbox.bind('<Double-Button-1>', self.copy_selected)
        
        # Control buttons
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x")
        
        ctk.CTkButton(control_frame, text="Copy Selected", command=self.copy_selected).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="View Details", command=self.view_details).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=5)
        
        # Status bar
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", font=("Inter", 10))
        self.status_label.pack(side="bottom", fill="x")
    
    def load_history(self):
        """Load history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
                self.update_history_list()
                self.status_label.configure(text=f"Loaded {len(self.history_data)} history entries")
            except Exception as e:
                self.status_label.configure(text=f"Error loading history: {e}")
    
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=2)
        except Exception as e:
            self.status_label.configure(text=f"Error saving history: {e}")
    
    def add_to_history(self, prompt, metadata=None):
        """Add prompt to history"""
        if not prompt.strip():  # Don't add empty prompts
            return
            
        history_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'prompt': prompt,
            'metadata': metadata or {},
            'prompt_preview': prompt[:150] + '...' if len(prompt) > 150 else prompt,
            'prompt_length': len(prompt)
        }
        
        # Add to beginning (most recent first)
        self.history_data.insert(0, history_entry)
        
        # Keep only last 100 entries
        self.history_data = self.history_data[:100]
        
        # Save and update
        self.save_history()
        self.update_history_list()
        self.status_label.configure(text=f"Added to history ({len(self.history_data)} total)")
    
    def update_history_list(self):
        """Update the history listbox"""
        self.history_listbox.delete(0, tk.END)
        
        for entry in self.history_data:
            timestamp = entry.get('timestamp', '')
            preview = entry.get('prompt_preview', '')
            length = entry.get('prompt_length', 0)
            
            # Format timestamp
            try:
                dt = datetime.datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_time = timestamp
            
            display_text = f"[{formatted_time}] [{length} chars] {preview}"
            self.history_listbox.insert(tk.END, display_text)
    
    def copy_selected(self, event=None):
        """Copy selected history entry to clipboard"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.history_data):
                prompt = self.history_data[index].get('prompt', '')
                if prompt:
                    self.main_window.root.clipboard_clear()
                    self.main_window.root.clipboard_append(prompt)
                    self.status_label.configure(text="Copied to clipboard")
                    self.main_window.set_status("History entry copied to clipboard")
        else:
            self.status_label.configure(text="No entry selected")
    
    def view_details(self):
        """View details of selected history entry"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.history_data):
                entry = self.history_data[index]
                prompt = entry.get('prompt', '')
                metadata = entry.get('metadata', {})
                timestamp = entry.get('timestamp', '')
                length = entry.get('prompt_length', 0)
                
                details = f"Timestamp: {timestamp}\n"
                details += f"Length: {length} characters\n\n"
                details += f"Prompt:\n{prompt}\n\n"
                if metadata:
                    details += f"Metadata:\n{json.dumps(metadata, indent=2)}"
                
                # Create details window
                details_window = tk.Toplevel(self.main_window.root)
                details_window.title("History Entry Details")
                details_window.geometry("600x400")
                
                text_widget = tk.Text(details_window, wrap=tk.WORD, width=70, height=20,
                                    bg="#1e1e1e", fg="#ffffff", insertbackground="white")
                scrollbar = tk.Scrollbar(details_window, orient="vertical")
                scrollbar.config(command=text_widget.yview)
                text_widget.config(yscrollcommand=scrollbar.set)
                
                scrollbar.pack(side="right", fill="y")
                text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                text_widget.insert("1.0", details)
                text_widget.config(state=tk.DISABLED)
        else:
            self.status_label.configure(text="No entry selected")
    
    def delete_selected(self):
        """Delete selected history entry"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.history_data):
                if messagebox.askyesno("Delete Entry", "Delete this history entry?"):
                    del self.history_data[index]
                    self.save_history()
                    self.update_history_list()
                    self.status_label.configure(text="Entry deleted")
        else:
            self.status_label.configure(text="No entry selected")
    
    def clear_history(self):
        """Clear all history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            count = len(self.history_data)
            self.history_data.clear()
            self.save_history()
            self.update_history_list()
            self.status_label.configure(text=f"Cleared {count} entries")
            self.main_window.set_status("History cleared")
    
    def refresh_history(self):
        """Refresh history display"""
        self.update_history_list()
        self.status_label.configure(text="History refreshed")
    
    def export_history(self):
        """Export history to file"""
        filename = filedialog.asksaveasfilename(
            parent=self.main_window.root,
            title="Export History",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.history_data, f, indent=2)
                self.status_label.configure(text=f"Exported to {os.path.basename(filename)}")
                self.main_window.set_status(f"History exported to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export history: {e}")
