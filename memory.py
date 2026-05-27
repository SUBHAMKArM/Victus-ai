"""Victus AI - Memory System"""
import json
import os
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(SCRIPT_DIR, "memory.json")
FAILED_FILE = os.path.join(SCRIPT_DIR, "failed_commands.json")


def _load(path):
    """Always returns a list. Fixes old dict format."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            # FIX: old format was {"conversations": [...]}
            if isinstance(data, dict):
                return data.get("conversations", [])
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def _save(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_memory():
    return _load(MEMORY_FILE)


def save_memory(user_text, ai_text):
    data = load_memory()
    data.append({
        "time": datetime.datetime.now().isoformat(),
        "user": user_text,
        "ai": ai_text
    })
    data = data[-200:]
    _save(MEMORY_FILE, data)


def save_failed(command):
    data = _load(FAILED_FILE)
    data.append({
        "time": datetime.datetime.now().isoformat(),
        "command": command
    })
    data = data[-100:]
    _save(FAILED_FILE, data)


def get_context(n=5):
    history = load_memory()[-n:]
    if not history:
        return ""
    lines = []
    for m in history:
        lines.append(f"User: {m.get('user', m.get('you', ''))}")
        lines.append(f"AI: {m.get('ai', '')}")
    return "\n".join(lines)