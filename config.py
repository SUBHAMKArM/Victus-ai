"""Victus AI - Configuration"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

WAKE_WORD = "victus"

# Exact wake variants (case-insensitive match)
WAKE_VARIANTS_EXACT = [
    "victus", "vikas", "vectus", "victor", "vickers",
    "victas", "vikto", "vikta", "vickus", "vitus",
    "victims", "vectors", "vicious", "victory"
]

# Two-word wake phrases that Google STT recognizes reliably
WAKE_PHRASES = [
    "hey victus", "hey vikas", "hey vectus", "hey victor",
    "hp victus", "hp vikas", "hp vectus",
    "ok victus", "ok vikas", "ok vectus",
    "hello victus", "hello vikas"
]

WAKE_FUZZY_THRESHOLD = 0.55

WAKE_BLACKLIST = [
    "pictures", "actress", "fitness", "status", "factory",
    "picture", "fixtures", "mixture", "texture", "lecture",
    "fracture", "structure", "capture", "feature", "vodafone",
    "actors", "actor", "active", "account", "action"
]

STOP_WORDS = ["stop", "stop victus", "bas", "chup", "quiet", "cancel", "thamo", "enough"]

# ══════════════════════════════════════════════════
#  AI BACKEND — LM Studio (primary) + Ollama (fallback)
# ══════════════════════════════════════════════════

# LM Studio uses OpenAI-compatible API at port 1234
LMSTUDIO_URL = "http://127.0.0.1:1234"

# Ollama (fallback if LM Studio not running)
OLLAMA_URL = "http://127.0.0.1:11434"

# Model preferences — LM Studio loads models by filename
# Set these to match what you have loaded in LM Studio
MODELS = {
    "fast": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
    "normal": "lmstudio-community/gemma-2-2b-it-GGUF",
    "heavy": "lmstudio-community/DeepSeek-R1-Distill-Qwen-7B-GGUF"
}

# Ollama model names (used if Ollama is the active backend)
MODELS_OLLAMA = {
    "fast": "tinyllama:latest",
    "normal": "gemma:2b",
    "heavy": "gpt-oss:20b"
}

MEMORY_FILE = "memory.json"
FAILED_FILE = "failed_commands.json"
EXCEL_FILE = "data.xlsx"

# ══════════════════════════════════════════════════
#  APIs
# ══════════════════════════════════════════════════
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Kolkata")
