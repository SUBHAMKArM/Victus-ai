"""
╔══════════════════════════════════════════════════╗
║  VICTUS AI - Hybrid Brain v4.0                   ║
║  LM Studio (primary) + Ollama (fallback)         ║
║  Auto-detects which backend is running            ║
║  OpenAI-compatible API for LM Studio              ║
║  Bengali/Hindi → never uses tiny models           ║
║  RAM-aware routing                                ║
╚══════════════════════════════════════════════════╝
"""
import requests
import time
import psutil
from config import MODELS, MODELS_OLLAMA, LMSTUDIO_URL, OLLAMA_URL
from memory import get_context


# ══════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════

AVAILABLE = []          # list of model IDs
BACKEND = None          # "lmstudio" or "ollama" or None
_active_url = None      # base URL of active backend
_active_models = None   # MODELS or MODELS_OLLAMA dict

LANG_NAMES = {"en": "English", "hi": "Hindi", "bn": "Bengali"}

SYSTEM_PROMPTS = {
    "en": (
        "You are Victus AI, a smart personal laptop assistant. "
        "Be helpful, confident, and concise. Max 2-3 sentences. "
        "If you don't know, say: I don't know that yet boss. "
        "Do NOT make up facts. Reply in English only."
    ),
    "hi": (
        "तुम Victus AI हो, एक स्मार्ट पर्सनल लैपटॉप सहायक। "
        "सहायक, आत्मविश्वासी और संक्षिप्त रहो। अधिकतम 2-3 वाक्य। "
        "अगर नहीं जानते तो बोलो: यह अभी नहीं जानता बॉस। "
        "कोई तथ्य मत बनाओ। सिर्फ हिंदी में जवाब दो।"
    ),
    "bn": (
        "তুমি Victus AI, একটি স্মার্ট পার্সোনাল ল্যাপটপ সহকারী। "
        "সহায়ক, আত্মবিশ্বাসী এবং সংক্ষিপ্ত হও। সর্বোচ্চ ২-৩ বাক্য। "
        "না জানলে বলো: এটা এখনো জানি না বস। "
        "কোনো তথ্য বানিও না। শুধু বাংলায় উত্তর দাও।"
    )
}


# ══════════════════════════════════════════════════
#  BACKEND DETECTION — LM Studio first, then Ollama
# ══════════════════════════════════════════════════

def _check_lmstudio():
    """Check if LM Studio is running and get loaded models."""
    try:
        r = requests.get(f"{LMSTUDIO_URL}/v1/models", timeout=3)
        if r.ok:
            data = r.json()
            models = [m["id"] for m in data.get("data", [])]
            return models if models else None
    except Exception:
        pass
    return None


def _check_ollama():
    """Check if Ollama is running and get available models."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.ok:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return None


def init():
    """
    Auto-detect backend:
    1. Try LM Studio (port 1234) first
    2. Fall back to Ollama (port 11434)
    3. Try starting Ollama if nothing found
    """
    global AVAILABLE, BACKEND, _active_url, _active_models
    import os

    # ── Try LM Studio first ──
    print("[*] Checking LM Studio (port 1234)...")
    models = _check_lmstudio()
    if models:
        AVAILABLE = models
        BACKEND = "lmstudio"
        _active_url = LMSTUDIO_URL
        _active_models = MODELS
        print(f"[*] ✓ LM Studio ONLINE | {len(models)} models loaded")
        for m in models:
            print(f"    • {m}")

        # Show language routing
        for lang in ["en", "hi", "bn"]:
            model = _pick_model("test question", lang=lang)
            print(f"  [ROUTE] {lang.upper()} → {model}")
        return True

    # ── Try Ollama ──
    print("[*] LM Studio not found. Checking Ollama (port 11434)...")
    models = _check_ollama()

    if models is None:
        print("[*] Starting Ollama...")
        os.system("start /min ollama serve")
        time.sleep(3)
        models = _check_ollama()

    if models:
        AVAILABLE = models
        BACKEND = "ollama"
        _active_url = OLLAMA_URL
        _active_models = MODELS_OLLAMA
        print(f"[*] ✓ Ollama ONLINE | {len(models)} models")
        for m in models:
            print(f"    • {m}")

        for lang in ["en", "hi", "bn"]:
            model = _pick_model("test question", lang=lang)
            print(f"  [ROUTE] {lang.upper()} → {model}")
        return True

    print("[!] Brain OFFLINE!")
    print("[!] Start LM Studio or run: ollama serve")
    return False


# ══════════════════════════════════════════════════
#  MODEL ROUTING
# ══════════════════════════════════════════════════

def _find_model(preferred_list):
    """Find first available model matching preferences."""
    for m in preferred_list:
        # Direct match
        if m in AVAILABLE:
            return m
        # Partial match (e.g. "gemma" in "gemma-2-2b-it-GGUF")
        base = m.split(":")[0].split("/")[-1].lower()
        for available in AVAILABLE:
            if base in available.lower():
                return available
    # Last resort
    return AVAILABLE[0] if AVAILABLE else None


def _is_tiny_model(model_name):
    """Check if model is too small for non-English."""
    if not model_name:
        return True
    tiny_markers = ["tinyllama", "tiny", "1b", "0.5b"]
    name_lower = model_name.lower()
    return any(marker in name_lower for marker in tiny_markers)


def _pick_model(text, lang="en"):
    """
    Smart model selection:
    - Bengali/Hindi → NEVER tiny models
    - English → fastest available model
    - RAM-aware: downgrades if RAM > 80%
    """
    if not AVAILABLE:
        return None

    words = len(text.split())
    ram = psutil.virtual_memory().percent
    models = _active_models or MODELS

    # ═══ NON-ENGLISH: need capable model ═══
    if lang in ("bn", "hi"):
        # Try preferred multilang models
        model = _find_model([models["normal"], models["heavy"]])

        # Safety: block tiny models for non-English
        if model and _is_tiny_model(model):
            print(f"  [BRAIN] ⚠️ Blocked tiny model for {lang}! Finding better...")
            for m in AVAILABLE:
                if not _is_tiny_model(m):
                    model = m
                    break

        if model and not _is_tiny_model(model):
            print(f"  [BRAIN] {lang.upper()} → {model}")
            return model

        # Last resort: use whatever is available (with warning)
        print(f"  [BRAIN] ⚠️ No good model for {lang}. Load a 2B+ model!")
        return AVAILABLE[0] if AVAILABLE else None

    # ═══ ENGLISH ═══
    if ram > 80:
        return _find_model([models["fast"], models["normal"]])

    if words <= 3:
        return _find_model([models["fast"], models["normal"]])
    elif words <= 10:
        return _find_model([models["normal"], models["fast"]])
    else:
        return _find_model([models["heavy"], models["normal"], models["fast"]])


# ══════════════════════════════════════════════════
#  ASK — Routes to correct backend automatically
# ══════════════════════════════════════════════════

def ask_ai(prompt, model=None, system_prompt=None):
    """
    Universal AI call. Routes to LM Studio or Ollama automatically.
    """
    if not model:
        model = AVAILABLE[0] if AVAILABLE else None
    if not model:
        return "Brain error: no model available"

    if BACKEND == "lmstudio":
        return _ask_lmstudio(prompt, model, system_prompt)
    elif BACKEND == "ollama":
        return _ask_ollama(prompt, model, system_prompt)
    else:
        return "Brain error: no backend connected"


def _ask_lmstudio(prompt, model, system_prompt=None):
    """Call LM Studio via OpenAI-compatible API."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        print(f"  [LM STUDIO] Calling {model}...")
        r = requests.post(
            f"{LMSTUDIO_URL}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.7,
                "stream": False
            },
            timeout=120
        )
        r.raise_for_status()
        data = r.json()
        answer = data["choices"][0]["message"]["content"].strip()
        print(f"  [LM STUDIO] Got response ({len(answer)} chars)")
        return answer

    except Exception as e:
        print(f"  [LM STUDIO] Error: {repr(e)}")
        return f"Brain error: {e}"


def _ask_ollama(prompt, model, system_prompt=None):
    """Call Ollama API (legacy support)."""
    try:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        print(f"  [OLLAMA] Calling {model}...")
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"num_predict": 200}
            },
            timeout=120
        )
        r.raise_for_status()
        answer = r.json().get("response", "").strip()
        print(f"  [OLLAMA] Got response ({len(answer)} chars)")
        return answer

    except Exception as e:
        print(f"  [OLLAMA] Error: {repr(e)}")
        return f"Brain error: {e}"


# Keep backward compatibility
def ask_ollama(prompt, model="tinyllama:latest"):
    """Legacy wrapper — routes through ask_ai."""
    return ask_ai(prompt, model)


# ══════════════════════════════════════════════════
#  THINK — Main reasoning with memory
# ══════════════════════════════════════════════════

def think_with_memory(text, lang="en"):
    """Think with memory + correct model for language."""
    if not AVAILABLE:
        print("  [BRAIN] No models!")
        return None

    model = _pick_model(text, lang=lang)
    if not model:
        print("  [BRAIN] No model found!")
        return None

    # Safety: block tiny for non-English
    if lang in ("bn", "hi") and _is_tiny_model(model):
        print(f"  [BRAIN] ⚠️ Blocked tiny model for {lang}!")
        return None

    context = get_context(5)
    system = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])
    lang_name = LANG_NAMES.get(lang, "English")

    user_prompt = f"""Past conversations:
{context}

User: {text}
Reply in {lang_name} (max 3 sentences, no filler, no letter format):"""

    print(f"  [BRAIN] Backend={BACKEND} | Model={model} | Lang={lang_name}")
    answer = ask_ai(user_prompt, model, system_prompt=system)

    if answer and not answer.startswith("Brain error:"):
        return _trim(answer)
    elif answer:
        print(f"  [BRAIN] Error: {answer}")
    return None


def detect_emotion(text):
    """Quick emotion detection."""
    if not AVAILABLE:
        return "neutral"
    models = _active_models or MODELS
    model = _find_model([models["fast"], models["normal"]])
    if not model:
        return "neutral"
    result = ask_ai(
        "Detect emotion. Reply ONE word only: happy sad angry neutral\n"
        f"Text: {text}",
        model)
    if result and not result.startswith("Brain error:"):
        for e in ["happy", "sad", "angry"]:
            if e in result.lower():
                return e
    return "neutral"


# ══════════════════════════════════════════════════
#  TRIM — Clean up AI responses
# ══════════════════════════════════════════════════

def _trim(answer):
    """Remove filler, hallucination, enforce length limit."""
    bad_openers = [
        "dear sir", "dear madam", "dear boss", "i am writing",
        "as an ai", "certainly!", "absolutely!", "of course!",
        "sure!", "example:", "<think>", "</think>"
    ]
    lower = answer.lower()

    # Remove <think>...</think> blocks (DeepSeek-R1 reasoning)
    import re
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()

    for bad in bad_openers:
        if lower.startswith(bad):
            lines = answer.split('\n')
            answer = '\n'.join(lines[2:]).strip() if len(lines) > 2 else answer
            break

    # Limit to ~300 chars for faster speech
    if len(answer) > 300:
        parts = answer[:300].rsplit('.', 1)
        answer = parts[0] + "." if len(parts) > 1 else answer[:300]

    return answer.strip()
