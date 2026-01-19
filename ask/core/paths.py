"""
core/paths.py

Definición de rutas base del proyecto.
Todas relativas al directorio ask/
"""

from pathlib import Path

# Directorio raíz del proyecto (ask/)
BASE_DIR = Path(__file__).resolve().parent.parent

PROMPT_MD = BASE_DIR / "prompt.md"
CUSTOM_MD = BASE_DIR / "custom.md"
AI_ENGINES_JSON = BASE_DIR / "ai_engines.json"
APP_STATE_JSON = BASE_DIR / "app_state.json"
