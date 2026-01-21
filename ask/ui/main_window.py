import customtkinter as ctk
from ui.tabs_main import MainTabs


class MainWindow(ctk.CTk):
    def __init__(self, app_state, history=None):
        super().__init__()

        self.app_state = app_state
        self.history = history

        self.title("Ask")
        self.geometry("1100x750")

        # MAIN TABS
        self.tabs = MainTabs(self, self.app_state, self.history)
        self.tabs.pack(fill="both", expand=True)

        # BOTTOM BAR (RESTORED + EXTENDED)
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=10, pady=6)

        self.generate_btn = ctk.CTkButton(
            bottom,
            text="Generate Prompt",
            command=self._generate_prompt
        )
        self.generate_btn.pack(side="left", padx=5)

        self.exit_btn = ctk.CTkButton(
            bottom,
            text="Exit Program",
            fg_color="red",
            command=self._exit
        )
        self.exit_btn.pack(side="right", padx=5)

    def _generate_prompt(self):
        # delegated to tabs (original behavior)
        if hasattr(self.tabs, "generate_prompt"):
            self.tabs.generate_prompt()

    def _exit(self):
        self.app_state.save()
        self.destroy()

