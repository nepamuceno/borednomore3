class PromptBuilder:
    def __init__(self, state, history):
        self.state = state
        self.history = history

    def build(self):
        rules = self.state.get("rules_text", "")
        prompt = self.state.get("prompt_text", "")

        context_files = []
        if self.state.get("include_context"):
            context_files = (
                self.state.get("pinned_context_files", []) +
                self.state.get("context_files", [])
            )

        final = "\n\n".join(
            p for p in [
                rules if self.state.get("include_rules") else "",
                prompt
            ] if p.strip()
        )

        self.history.add(prompt, rules, context_files)
        return final

