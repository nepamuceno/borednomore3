import customtkinter as ctk


class ContextTab(ctk.CTkFrame):
    def __init__(self, parent, state):
        super().__init__(parent)
        self.state = state

        self.listbox = ctk.CTkTextbox(self)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        self._render()

    def _render(self):
        self.listbox.delete("1.0", "end")

        context_files = self.state.get("context_files", [])

        for ctx in context_files:
            # OLD FORMAT: string path
            if isinstance(ctx, str):
                self.listbox.insert("end", f"{ctx}\n")
                continue

            # NEW FORMAT: dict
            pin = "📌 " if ctx.get("pinned", False) else ""
            path = ctx.get("path", "")
            self.listbox.insert("end", f"{pin}{path}\n")

