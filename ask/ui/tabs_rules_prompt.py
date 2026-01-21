import customtkinter as ctk
from tkinter import filedialog

class RulesPromptTab(ctk.CTkFrame):
    def __init__(self, parent, state, key):
        super().__init__(parent)
        self.state = state
        self.key = key
        self.undo_stack = []
        self.redo_stack = []

        self.text = ctk.CTkTextbox(self)
        self.text.pack(fill="both", expand=True)

        btns = ctk.CTkFrame(self)
        btns.pack(fill="x")

        ctk.CTkButton(btns, text="Load", command=self.load).pack(side="left")
        ctk.CTkButton(btns, text="Save", command=self.save).pack(side="left")
        ctk.CTkButton(btns, text="Save As", command=self.save_as).pack(side="left")
        ctk.CTkButton(btns, text="Undo", command=self.undo).pack(side="left")
        ctk.CTkButton(btns, text="Redo", command=self.redo).pack(side="left")

        # LOAD STATE ON START
        self.text.insert("1.0", self.state.get(self.key, ""))

        self.text.bind("<<Modified>>", self.on_change)

    def on_change(self, _=None):
        content = self.text.get("1.0", "end")
        if not self.undo_stack or self.undo_stack[-1] != content:
            self.undo_stack.append(content)
            self.redo_stack.clear()
        self.text.edit_modified(False)

    def load(self):
        path = filedialog.askopenfilename()
        if path:
            content = open(path, "r", encoding="utf-8").read()
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.state.set(self.key, content)

    def save(self):
        self.state.set(self.key, self.text.get("1.0", "end"))

    def save_as(self):
        path = filedialog.asksaveasfilename()
        if path:
            open(path, "w", encoding="utf-8").write(self.text.get("1.0", "end"))

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.text.delete("1.0", "end")
            self.text.insert("1.0", self.undo_stack[-1])

    def redo(self):
        if self.redo_stack:
            content = self.redo_stack.pop()
            self.undo_stack.append(content)
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)

