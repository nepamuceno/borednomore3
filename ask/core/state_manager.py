"""
core/state_manager.py

Gestión de estado persistente de la aplicación.
Guarda y carga app_state.json.
"""

import json
from typing import Any, Dict

from core.paths import APP_STATE_JSON


class StateManager:
    def __init__(self) -> None:
        self._state: Dict[str, Any] = {
            "history": [],
            "context_files": []
        }
        self.load()

    # -----------------------------------------------------

    def load(self) -> None:
        if not APP_STATE_JSON.exists():
            return

        try:
            data = json.loads(
                APP_STATE_JSON.read_text(encoding="utf-8")
            )
            if isinstance(data, dict):
                self._state.update(data)
        except Exception:
            # Estado corrupto → ignorar y seguir con defaults
            pass

    def save(self) -> None:
        APP_STATE_JSON.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # -----------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value
