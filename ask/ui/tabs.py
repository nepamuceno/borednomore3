import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from ui.widgets import TextEditor

class MainTabs(ctk.CTkTabview):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state

        self.rules = self.add("Rules")
        self.prompt = self.add("Prompt")
        self.context = self.add("Context")
        self.history = self.add("History")

        self.build_rules()
        self.build_prompt()
        self.build_context()
        self.build_history()

    def build_rules(self):
        e = TextEditor(self.rules)
        e.pack(fill="both", expand=True)
        e.insert("1.0", self.state.get("rules_text"))
        e.bind("<KeyRelease>", lambda _: self.state.set("rules_text", e.get("1.0","end")))

    def build_prompt(self):
        e = TextEditor(self.prompt)
        e.pack(fill="both", expand=True)
        e.insert("1.0", self.state.get("prompt_text"))
        e.bind("<KeyRelease>", lambda _: self.state.set("prompt_text", e.get("1.0","end")))

    def build_context(self):
        lb = tk.Listbox(self.context)
        lb.pack(fill="both", expand=True)

        for f in self.state.get("context_files"):
            lb.insert("end", f)

        def add():
            f = filedialog.askopenfilename()
            if f:
                self.state.append("context_files", f)
                lb.insert("end", f)

        def pin():
            if lb.curselection():
                self.state.append("pinned_context_files", lb.get(lb.curselection()))

        ctk.CTkButton(self.context, text="Add", command=add).pack(side="left")
        ctk.CTkButton(self.context, text="Pin", command=pin).pack(side="left")

    def build_history(self):
        lb = tk.Listbox(self.history)
        lb.pack(fill="both", expand=True)
        for i, _ in enumerate(self.state.get("history")):
            lb.insert("end", f"Prompt {i+1}")

