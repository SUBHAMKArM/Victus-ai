"""Test all imports and brain backend detection for v7.0"""
import sys, os
sys.path.insert(0, r'C:\Users\sarmi\.gemini\antigravity\scratch\victus-ai-assistant')
os.chdir(r'C:\Users\sarmi\.gemini\antigravity\scratch\victus-ai-assistant')
os.environ['HF_HUB_DISABLE_XET'] = '1'

print('=== VICTUS AI v7.0 — IMPORT TEST ===')
print()

# 1. config
from config import (STOP_WORDS, WAKE_VARIANTS_EXACT, WAKE_PHRASES,
                     WAKE_BLACKLIST, WAKE_FUZZY_THRESHOLD,
                     MODELS, MODELS_OLLAMA, LMSTUDIO_URL, OLLAMA_URL)
print('[OK] config.py')
print(f'     LM Studio URL: {LMSTUDIO_URL}')
print(f'     Ollama URL:    {OLLAMA_URL}')
print(f'     LM Models:     {MODELS}')
print(f'     Ollama Models:  {MODELS_OLLAMA}')

# 2. memory
from memory import save_memory, save_failed, get_context
print('[OK] memory.py')

# 3. actions
from actions import handle_command
print('[OK] actions.py')

# 4. excel_ai
from excel_ai import handle_excel
print('[OK] excel_ai.py')

# 5. vision
from vision import handle_vision, init_vision
print('[OK] vision.py')

# 6. brain — NEW dual backend
from brain import (init as init_brain, think_with_memory, detect_emotion,
                   AVAILABLE, BACKEND, ask_ai, _pick_model, ask_ollama)
print('[OK] brain.py')

# 7. voice
print()
print('=== Testing voice.py imports ===')
try:
    from voice import (speak, listen, listen_passive, beep, boot_beep,
                       is_wake, extract_after_wake, clean, get_current_lang,
                       _set_lang)
    print('[OK] voice.py')
except Exception as e:
    print(f'[FAIL] voice.py: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 8. Test assistant.py imports
print()
print('=== Testing assistant.py imports ===')
try:
    # Simulate what assistant.py does
    from brain import (init as init_brain2, think_with_memory as twm2,
                       detect_emotion as de2, AVAILABLE as av2,
                       BACKEND as be2, ask_ai as aa2, _pick_model as pm2)
    print('[OK] assistant.py brain imports work')
except Exception as e:
    print(f'[FAIL] {e}')

# 9. Brain init
print()
print('=== Testing Brain Backend Detection ===')
init_brain()
print(f'  Backend: {BACKEND}')
print(f'  Models:  {AVAILABLE}')

if AVAILABLE:
    print()
    print('=== Model Routing Test ===')
    for lang in ["en", "hi", "bn"]:
        model = _pick_model("test question here", lang=lang)
        print(f'  {lang.upper()} → {model}')

    # Try a quick API call
    print()
    print('=== Quick API Test ===')
    model = AVAILABLE[0]
    result = ask_ai("Say hello in one word", model)
    print(f'  Model: {model}')
    print(f'  Response: {result[:100]}')

print()
print('=== ALL TESTS COMPLETE ===')
