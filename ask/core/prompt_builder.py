"""
core/prompt_builder.py

Construye el prompt final a partir de:
- prompt.md (rules)
- custom.md (custom instructions)
- contexto cargado
"""

from core.paths import PROMPT_MD, CUSTOM_MD
from core.state_manager import StateManager


class PromptBuilder:
    def __init__(self, state: StateManager) -> None:
        self.state = state

    # -------------------------------------------------

    def build_prompt(self, context: str) -> str:
        sections = []

        # Rules
        if PROMPT_MD.exists():
            text = PROMPT_MD.read_text(encoding="utf-8").strip()
            if text:
                sections.append(text)

        # Custom
        if CUSTOM_MD.exists():
            text = CUSTOM_MD.read_text(encoding="utf-8").strip()
            if text:
                sections.append(text)

        # Context
        if context.strip():
            sections.append("### Context\n" + context.strip())

        return "\n\n".join(sections)
