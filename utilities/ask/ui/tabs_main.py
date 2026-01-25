import customtkinter as ctk
from ui.tabs_rules_prompt import RulesPromptTab
from ui.tabs_context import ContextTab
from ui.tabs_history import HistoryTab
from ui.tabs_ai_engines import AITab

class MainTabs(ctk.CTkTabview):
    def __init__(self, parent, state, history):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        self.add("Rules")
        self.add("Prompt")
        self.add("Context")
        self.add("History")
        self.add("AI Engines")

        RulesPromptTab(self.tab("Rules"), state, "rules_text").pack(fill="both", expand=True)
        RulesPromptTab(self.tab("Prompt"), state, "prompt_text").pack(fill="both", expand=True)
        ContextTab(self.tab("Context"), state).pack(fill="both", expand=True)
        HistoryTab(self.tab("History"), history).pack(fill="both", expand=True)
        AITab(self.tab("AI Engines"), state).pack(fill="both", expand=True)

