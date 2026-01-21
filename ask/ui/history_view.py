import customtkinter as ctk
from ui.widgets import TextEditor

class HistoryView(ctk.CTkScrollableFrame):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state
        self.refresh()

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        for i, entry in enumerate(self.state.get("history")):
            btn = ctk.CTkButton(
                self,
                text=f"Prompt {i+1}",
                command=lambda idx=i: self.toggle(idx)
            )
            btn.pack(fill="x")

            if isinstance(entry, dict) and not entry.get("collapsed", True):
                t = TextEditor(self)
                t.pack(fill="x")
                t.insert("1.0", entry["content"])
                t.configure(state="disabled")

    def toggle(self, idx):
        e = self.state.get("history")[idx]
        if isinstance(e, dict):
            e["collapsed"] = not e.get("collapsed", True)
            self.state.save()
            self.refresh()

