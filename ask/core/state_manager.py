import json
import os
import threading
import time

STATE_FILE = "app_state.json"
AI_ENGINES_FILE = "ai_engines.json"
AUTOSAVE_SECONDS = 300

class StateManager:
    """
    Global persistent application state manager.
    """

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.path = os.path.join(base_dir, STATE_FILE)
        self.ai_path = os.path.join(base_dir, AI_ENGINES_FILE)

        self.state = {
            "theme": "system",
            "rules_text": "",
            "prompt_text": "",
            "context_files": [],
            "pinned_context_files": [],
            "include_rules": True,
            "include_context": True,
            "ai_engines": []
        }

        self._load_state()
        self._load_ai_engines()
        self._start_autosave()

    def _load_state(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.state.update(json.load(f))

    def _load_ai_engines(self):
        if os.path.exists(self.ai_path):
            with open(self.ai_path, "r", encoding="utf-8") as f:
                self.state["ai_engines"] = json.load(f)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

        with open(self.ai_path, "w", encoding="utf-8") as f:
            json.dump(self.state.get("ai_engines", []), f, indent=2)

    def _start_autosave(self):
        def loop():
            while True:
                time.sleep(AUTOSAVE_SECONDS)
                self.save()
        threading.Thread(target=loop, daemon=True).start()

    def get(self, key, default=None):
        return self.state.get(key, default)

    def set(self, key, value):
        self.state[key] = value
        self.save()
