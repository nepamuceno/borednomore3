import json
from pathlib import Path

ENGINES_FILE = Path("ai_engines.json")

def load_engines():
    return json.loads(ENGINES_FILE.read_text())

def save_engines(data):
    ENGINES_FILE.write_text(json.dumps(data, indent=2))

