"""Victus AI - Hybrid Brain"""
import requests
import subprocess
import time
import psutil
from config import MODELS, OLLAMA_URL
from memory import get_context

AVAILABLE = []


def _wait_for_ollama(timeout=30):
    """Wait for Ollama to be fully ready."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if r.ok:
                return r.json().get("models", [])
        except Exception:
            pass
        time.sleep(2)
    return None


def init():
    """Start Ollama and wait for it to be ready."""
    global AVAILABLE
    import os

    print("[*] Connecting to Ollama brain...")
    models = _wait_for_ollama(timeout=5)

    if models is None:
        print("[*] Starting Ollama...")
        os.system("start /min ollama serve")
        models = _wait_for_ollama(timeout=30)

    if models:
        AVAILABLE = [m["name"] for m in models]
        print(f"[*] Brain ONLINE. Models: {AVAILABLE}")
        return True

    # Last resort
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")[1:]
            AVAILABLE = [line.split()[0] for line in lines if line.strip()]
            print(f"[*] Brain ONLINE (subprocess). Models: {AVAILABLE}")
            return True
    except Exception:
        pass

    print("[!] Brain OFFLINE. Run: ollama pull tinyllama")
    return False


def _find_model(preferred_list):
    """Find first available model. Handles name:tag format."""
    for m in preferred_list:
        # Exact match first
        if m in AVAILABLE:
            return m
        # Partial match (tinyllama matches tinyllama:latest)
        for available in AVAILABLE:
            if m.split(":")[0] in available:
                return available
    return AVAILABLE[0] if AVAILABLE else None


def ask_ollama(prompt, model="tinyllama:latest"):
    """Direct Ollama API call. Shows real error on failure."""
    try:
        print(f"  [OLLAMA] Calling {model}...")
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"num_predict": 150}},
            timeout=120
        )
        r.raise_for_status()
        answer = r.json().get("response", "").strip()
        print(f"  [OLLAMA] Got response ({len(answer)} chars)")
        return answer
    except Exception as e:
        print(f"  [OLLAMA DEBUG] {repr(e)}")
        return f"Brain error: {e}"


def think_with_memory(text):
    """Think with past conversation context."""
    if not AVAILABLE:
        print("  [BRAIN] No models available!")
        return None

    model = _pick_model(text)
    if not model:
        print("  [BRAIN] Could not find a model!")
        return None

    context = get_context(5)
    prompt = f"""You are Victus AI, a personal assistant. Be helpful, confident, concise.
Reply in the same language the user speaks (English/Hindi/Bengali).

Past conversations:
{context}

User: {text}
Reply:"""

    print(f"  [BRAIN] Using {model}...")
    answer = ask_ollama(prompt, model)

    # Don't return error messages as "no brain" — return them as actual responses
    if answer and not answer.startswith("Brain error:"):
        return _trim(answer)
    elif answer:
        print(f"  [BRAIN] {answer}")
    return None


def _pick_model(text):
    """3-layer routing + RAM-aware."""
    words = len(text.split())
    ram = psutil.virtual_memory().percent

    if ram > 80:
        return _find_model([MODELS["fast"], MODELS["normal"]])

    if words <= 3:
        return _find_model([MODELS["fast"], MODELS["normal"]])
    elif words <= 10:
        return _find_model([MODELS["normal"], MODELS["fast"]])
    else:
        return _find_model([MODELS["heavy"], MODELS["normal"], MODELS["fast"]])


def detect_emotion(text):
    if not AVAILABLE:
        return "neutral"
    model = _find_model([MODELS["fast"], MODELS["normal"]])
    if not model:
        return "neutral"
    result = ask_ollama(
        f"Detect emotion. Reply ONE word: happy, sad, angry, or neutral.\nText: {text}",
        model)
    if result and not result.startswith("Brain error:"):
        for e in ["happy", "sad", "angry"]:
            if e in result.lower():
                return e
    return "neutral"


def _trim(answer):
    if answer and len(answer) > 400:
        parts = answer[:400].rsplit('.', 1)
        answer = parts[0] + "." if len(parts) > 1 else answer[:400]
    return answer