import customtkinter as ctk

class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, history):
        super().__init__(parent)
        self.history = history

        self.box = ctk.CTkTextbox(self)
        self.box.pack(fill="both", expand=True)

        self.box.bind("<Button-1>", self.toggle)
        self.refresh()

    def refresh(self):
        self.box.delete("1.0", "end")
        for i, h in enumerate(self.history.history):
            self.box.insert(
                "end",
                f"{i}. [{h['timestamp']}] {h['title']}\n"
            )
            if h["expanded"]:
                self.box.insert(
                    "end",
                    f"   Rules length: {h['rules_len']}\n"
                    f"   Context files: {', '.join(h['context_files'])}\n\n"
                )

    def toggle(self, event):
        idx = int(self.box.index(f"@{event.x},{event.y}").split(".")[0]) - 1
        if 0 <= idx < len(self.history.history):
            self.history.history[idx]["expanded"] ^= True
            self.history.save()
            self.refresh()

