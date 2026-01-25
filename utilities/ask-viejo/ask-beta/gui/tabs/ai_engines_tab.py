"""
AI Engines Tab - COMPLETE WORKING VERSION
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import json
import os

class AiEnginesTab:
    def __init__(self, parent, main_window, ai_engines_data=None):
        self.parent = parent
        self.main_window = main_window
        self.ai_engines_data = ai_engines_data or []
        
        self.create_widgets()
        self.populate_ai_engines()
    
    def create_widgets(self):
        """Create AI engines widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="AI Engines Configuration", 
                                  font=("Inter", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create Treeview with Scrollbars
        tree_scroll_y = tk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side="right", fill="y")
        
        tree_scroll_x = tk.Scrollbar(tree_frame, orientation="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")
        
        self.ai_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, 
                                   xscrollcommand=tree_scroll_x.set, height=15)
        tree_scroll_y.configure(command=self.ai_tree.yview)
        tree_scroll_x.configure(command=self.ai_tree.xview)
        
        # Define columns
        self.ai_tree['columns'] = ('name', 'model', 'api_key', 'endpoint', 'enabled')
        self.ai_tree.column('#0', width=0, stretch=tk.NO)
        self.ai_tree.column('name', anchor=tk.W, width=150)
        self.ai_tree.column('model', anchor=tk.W, width=200)
        self.ai_tree.column('api_key', anchor=tk.W, width=250)
        self.ai_tree.column('endpoint', anchor=tk.W, width=300)
        self.ai_tree.column('enabled', anchor=tk.CENTER, width=80)
        
        # Create headings
        self.ai_tree.heading('#0', text='', anchor=tk.W)
        self.ai_tree.heading('name', text='Name', anchor=tk.W)
        self.ai_tree.heading('model', text='Model', anchor=tk.W)
        self.ai_tree.heading('api_key', text='API Key', anchor=tk.W)
        self.ai_tree.heading('endpoint', text='Endpoint', anchor=tk.W)
        self.ai_tree.heading('enabled', text='Enabled', anchor=tk.CENTER)
        
        self.ai_tree.pack(fill="both", expand=True)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(buttons_frame, text="Add Engine", 
                     command=self.add_engine).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Edit Engine", 
                     command=self.edit_engine).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Delete Engine", 
                     command=self.delete_engine).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Save Changes", 
                     command=self.save_engines).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Load Default", 
                     command=self.load_default_engines).pack(side="left", padx=5)
        
        # Status bar
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", font=("Inter", 10))
        self.status_label.pack(side="bottom", fill="x")
    
    def populate_ai_engines(self):
        """Populate the treeview with AI engines data"""
        # Clear existing items
        for item in self.ai_tree.get_children():
            self.ai_tree.delete(item)
        
        # Add engines from data
        for engine in self.ai_engines_data:
            self.ai_tree.insert('', 'end', values=(
                engine.get('name', ''),
                engine.get('model', ''),
                self.mask_api_key(engine.get('api_key', '')),
                engine.get('endpoint', ''),
                '✓' if engine.get('enabled', False) else '✗'
            ))
        
        self.status_label.configure(text=f"Loaded {len(self.ai_engines_data)} AI engines")
    
    def mask_api_key(self, api_key):
        """Mask API key for display"""
        if len(api_key) > 8:
            return api_key[:4] + '****' + api_key[-4:]
        else:
            return '****'
    
    def add_engine(self):
        """Add new AI engine"""
        dialog = ctk.CTkInputDialog(text="Enter engine name:", title="Add AI Engine")
        name = dialog.get_input()
        
        if name:
            dialog = ctk.CTkInputDialog(text="Enter model name:", title="Add AI Engine")
            model = dialog.get_input()
            
            if model:
                dialog = ctk.CTkInputDialog(text="Enter API key:", title="Add AI Engine")
                api_key = dialog.get_input()
                
                if api_key:
                    dialog = ctk.CTkInputDialog(text="Enter endpoint URL:", title="Add AI Engine")
                    endpoint = dialog.get_input()
                    
                    if endpoint:
                        new_engine = {
                            'name': name,
                            'model': model,
                            'api_key': api_key,
                            'endpoint': endpoint,
                            'enabled': True
                        }
                        
                        self.ai_engines_data.append(new_engine)
                        self.populate_ai_engines()
                        self.status_label.configure(text=f"Added engine: {name}")
                        self.main_window.set_status(f"Added AI engine: {name}")
    
    def edit_engine(self):
        """Edit selected AI engine"""
        selection = self.ai_tree.selection()
        if selection:
            item = selection[0]
            values = self.ai_tree.item(item)['values']
            
            if values:
                # Get new values
                dialog = ctk.CTkInputDialog(text=f"Edit name ({values[0]}):", title="Edit AI Engine")
                name = dialog.get_input()
                
                if name:
                    dialog = ctk.CTkInputDialog(text=f"Edit model ({values[1]}):", title="Edit AI Engine")
                    model = dialog.get_input()
                    
                    if model:
                        dialog = ctk.CTkInputDialog(text="Enter new API key (or leave blank to keep current):", title="Edit AI Engine")
                        api_key = dialog.get_input()
                        
                        dialog = ctk.CTkInputDialog(text=f"Edit endpoint ({values[3]}):", title="Edit AI Engine")
                        endpoint = dialog.get_input()
                        
                        if endpoint:
                            # Find and update the engine
                            for engine in self.ai_engines_data:
                                if engine['name'] == values[0] and engine['model'] == values[1]:
                                    engine['name'] = name
                                    engine['model'] = model
                                    if api_key and api_key != '':
                                        engine['api_key'] = api_key
                                    engine['endpoint'] = endpoint
                                    break
                            
                            self.populate_ai_engines()
                            self.status_label.configure(text=f"Updated engine: {name}")
        else:
            messagebox.showwarning("No Selection", "Please select an engine to edit")
    
    def delete_engine(self):
        """Delete selected AI engine"""
        selection = self.ai_tree.selection()
        if selection:
            item = selection[0]
            values = self.ai_tree.item(item)['values']
            
            if values and messagebox.askyesno("Delete Engine", f"Delete engine '{values[0]}'?"):
                # Find and remove the engine
                self.ai_engines_data = [e for e in self.ai_engines_data 
                                       if not (e['name'] == values[0] and e['model'] == values[1])]
                
                self.populate_ai_engines()
                self.status_label.configure(text=f"Deleted engine: {values[0]}")
                self.main_window.set_status(f"Deleted AI engine: {values[0]}")
        else:
            messagebox.showwarning("No Selection", "Please select an engine to delete")
    
    def save_engines(self):
        """Save AI engines to file"""
        try:
            with open(self.main_window.ai_engines_path, 'w', encoding='utf-8') as f:
                json.dump(self.ai_engines_data, f, indent=2)
            
            self.status_label.configure(text=f"Saved {len(self.ai_engines_data)} engines")
            self.main_window.set_status("AI engines configuration saved")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save engines: {e}")
    
    def load_default_engines(self):
        """Load default AI engines"""
        default_engines = [
            {
                "name": "OpenAI GPT-4",
                "model": "gpt-4",
                "api_key": "your-openai-api-key-here",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "enabled": False
            },
            {
                "name": "Anthropic Claude",
                "model": "claude-3-sonnet-20240229",
                "api_key": "your-anthropic-api-key-here",
                "endpoint": "https://api.anthropic.com/v1/messages",
                "enabled": False
            },
            {
                "name": "Local Ollama",
                "model": "llama2",
                "api_key": "ollama",
                "endpoint": "http://localhost:11434/api/generate",
                "enabled": False
            }
        ]
        
        self.ai_engines_data = default_engines
        self.populate_ai_engines()
        self.status_label.configure(text="Loaded default engines")
        self.main_window.set_status("Loaded default AI engines")
