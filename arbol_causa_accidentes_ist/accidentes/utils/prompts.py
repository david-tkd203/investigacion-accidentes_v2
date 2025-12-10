import json
from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parent.parent / "setting" / "prompt" / "prompt.json"

def cargar_prompts():
    with open(PROMPT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("prompts", {})
