import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"

class HistoryManager:
    def __init__(self, base_dir):
        self.path = os.path.join(base_dir, HISTORY_FILE)
        self.history = []
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # MIGRATE OLD STRING ENTRIES
                    for h in data:
                        if isinstance(h, dict):
                            self.history.append(h)
            except Exception:
                pass

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def add(self, prompt, rules, context_files):
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "title": prompt.splitlines()[0][:80] if prompt else "",
            "rules_len": len(rules),
            "context_files": context_files,
            "expanded": False
        }
        self.history.insert(0, entry)
        self.save()

