"""Victus AI - Configuration"""

WAKE_WORD = "victus"
WAKE_VARIANTS = ["victus", "vikas", "vectus", "victor", "vickers"]

MODELS = {
    "fast": "tinyllama:latest",
    "normal": "gemma:2b",
    "heavy": "gpt-oss:20b"
}

OLLAMA_URL = "http://127.0.0.1:11434"
MEMORY_FILE = "memory.json"
FAILED_FILE = "failed_commands.json"
EXCEL_FILE = "data.xlsx"