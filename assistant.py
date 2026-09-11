"""
╔══════════════════════════════════════════╗
║  VICTUS AI - JARVIS v7.0                 ║
║  LM Studio + Ollama (auto-detect)        ║
║  "Hey Victus" wake phrase                 ║
║  Bengali/Hindi/English multi-lang         ║
╚══════════════════════════════════════════╝
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
os.environ["HF_HUB_DISABLE_XET"] = "1"

from config import STOP_WORDS
from hud import init_hud, set_hud_status
from voice import (speak, listen, listen_passive, beep, boot_beep,
                   is_wake, extract_after_wake, clean, get_current_lang,
                   _set_lang)
from brain import (init as init_brain, think_with_memory, detect_emotion,
                   AVAILABLE, BACKEND, ask_ai, _pick_model)
from actions import handle_command
from excel_ai import handle_excel
from vision import handle_vision, init_vision
from memory import save_memory, save_failed


def is_stop(text):
    t = text.lower().strip()
    return any(w in t for w in STOP_WORDS)


def is_lang_switch(text):
    t = text.lower()
    if any(w in t for w in ["speak bengali", "bangla bolo", "bangla mode", "bengali mode"]):
        _set_lang("bn")
        return True, "bn"
    if any(w in t for w in ["speak hindi", "hindi bolo", "hindi mode"]):
        _set_lang("hi")
        return True, "hi"
    if any(w in t for w in ["speak english", "english mode", "english bolo"]):
        _set_lang("en")
        return True, "en"
    return False, None


def process(text):
    """Universal router: stop → lang → system → excel → vision → brain."""
    set_hud_status("THINKING")

    if is_stop(text):
        speak("Okay boss, going silent.")
        return

    switched, lang = is_lang_switch(text)
    if switched:
        lang_names = {"en": "English", "hi": "Hindi", "bn": "Bengali"}
        speak(f"Switched to {lang_names[lang]} mode boss.")
        return

    lang = get_current_lang()

    # Layer 1: System commands
    handled, response = handle_command(text)
    if handled:
        speak(response)
        save_memory(text, response)
        return

    # Layer 2: Excel
    handled, response = handle_excel(text)
    if handled:
        speak(response)
        save_memory(text, response)
        return

    # Layer 3: Vision
    handled, response = handle_vision(text)
    if handled:
        speak(response)
        save_memory(text, response)
        return

    # Layer 4: AI brain (uses correct model per language)
    if AVAILABLE:
        reply = think_with_memory(text, lang=lang)
        if reply:
            speak(reply)
            save_memory(text, reply)
            return

    # Layer 5: Direct fallback
    model = _pick_model(text, lang=lang) if AVAILABLE else None
    if model:
        direct = ask_ai(text, model)
    else:
        direct = None
    if direct and not direct.startswith("Brain error:"):
        speak(direct)
        save_memory(text, direct)
        return

    save_failed(text)
    speak("Sorry boss, my brain could not process that.")


def main():
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║     VICTUS AI - JARVIS v7.0               ║")
    print("  ║     LM Studio + Multi-Language AI OS       ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    init_brain()

    print("  [*] Initializing Vision AI...")
    init_vision()
    
    print("  [*] Initializing HUD...")
    def on_image_upload(file_path):
        from vision import analyze_image
        set_hud_status("THINKING")
        res = analyze_image(file_path)
        set_hud_status("SPEAKING")
        speak("I see " + res)
        set_hud_status("LISTENING")
        
    init_hud(on_image_upload)

    boot_beep()

    print()
    backend_name = BACKEND.upper() if BACKEND else "OFFLINE"
    print(f"  [*] Backend: {backend_name} | {len(AVAILABLE)} models" if AVAILABLE else "  [*] Brain: OFFLINE")
    print(f"  [*] Models: {AVAILABLE}")
    print()

    speak(f"Victus AI online. {backend_name} backend with {len(AVAILABLE)} models.")

    print()
    print("  ┌────────────────────────────────────────────┐")
    print("  │  Wake words:                               │")
    print("  │    'Hey Victus ...'  (BEST - Google hears!)│")
    print("  │    'Hello Victus ...'(Also very reliable)  │")
    print("  │    'Victus ...'      (sometimes misheard)  │")
    print("  │                                            │")
    print("  │  Language: 'Hey Victus speak bengali'      │")
    print("  │  Stop:     'Stop' / 'Bas' / 'Chup'         │")
    print("  └────────────────────────────────────────────┘")
    print()
    print("  ══════════════════════════════════════════")
    print("  ✓ READY — Say 'Hey Victus' or 'Hello Victus'!")
    print("  ══════════════════════════════════════════")
    print()

    while True:
        try:
            heard = listen_passive()
            if not heard:
                continue

            # Stop check
            if is_stop(heard):
                print("  [*] Stop heard. Ignoring.")
                continue

            if is_wake(heard):
                command = extract_after_wake(heard)

                if command:
                    if is_stop(command):
                        speak("Okay boss.")
                        continue

                    beep()
                    speak("Yes boss!")
                    command = clean(command)
                    process(command)

                else:
                    beep()
                    speak("Yes boss?")

                    command = listen(timeout=7, phrase_limit=10)
                    if command:
                        if is_stop(command):
                            speak("Okay boss.")
                            continue
                        command = clean(command)
                        process(command)
                    else:
                        speak("I didn't catch that.")

                print()
                print("  [*] Listening for 'Hey Victus' / 'Hello Victus'...")

        except KeyboardInterrupt:
            speak("Goodbye boss.")
            break
        except Exception as e:
            print(f"[!] {e}")
            import traceback
            traceback.print_exc()
            import time
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()
