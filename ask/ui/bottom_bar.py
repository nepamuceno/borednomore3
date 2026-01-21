import customtkinter as ctk

class BottomBar(ctk.CTkFrame):
    def __init__(self, parent, state):
        super().__init__(parent)
        self.state = state

        self.rules = ctk.CTkCheckBox(
            self, text="Include Rules",
            command=lambda: self.toggle("include_rules")
        )
        self.rules.select()
        self.rules.pack(side="left", padx=5)

        self.context = ctk.CTkCheckBox(
            self, text="Include Context",
            command=lambda: self.toggle("include_context")
        )
        self.context.select()
        self.context.pack(side="left", padx=5)

    def toggle(self, key):
        self.state.set(key, not self.state.get(key))

