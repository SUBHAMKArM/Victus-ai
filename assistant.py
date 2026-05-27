"""
╔══════════════════════════════════════════╗
║  VICTUS AI - FINAL JARVIS SYSTEM         ║
║  Voice + Brain + Memory + Excel + Vision ║
║  v5.0 — Iron Man Edition                 ║
╚══════════════════════════════════════════╝
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from voice import speak, listen, listen_passive, beep, boot_beep, is_wake, extract_after_wake, clean
from brain import init as init_brain, think_with_memory, detect_emotion, AVAILABLE
from actions import handle_command
from excel_ai import handle_excel
from vision import handle_vision, init_vision
from memory import save_memory, save_failed


# ── Language detection (optional) ──
HAS_LANG = False
try:
    from langdetect import detect as detect_lang
    HAS_LANG = True
except ImportError:
    pass


def process(text):
    """Universal task handler: system → excel → vision → AI brain."""

    # Layer 1: System commands (instant, no AI)
    handled, response = handle_command(text)
    if handled:
        speak(response)
        save_memory(text, response)
        return

    # Layer 2: Excel automation
    handled, response = handle_excel(text)
    if handled:
        speak(response)
        save_memory(text, response)
        return

    # Layer 3: Vision / Image analysis
    handled, response = handle_vision(text)
    if handled:
        speak(response)
        save_memory(text, response)
        return

    # Layer 4: AI brain (with memory context)
    if AVAILABLE:
        emotion = detect_emotion(text)
        reply = think_with_memory(text)
        if reply:
            speak(reply, emotion=emotion)
            save_memory(text, reply)
            return

    # Layer 5: Brain failed or offline
    from brain import ask_ollama
    # One last direct attempt
    direct = ask_ollama(text, "tinyllama:latest")
    if direct and not direct.startswith("Brain error:"):
        speak(direct)
        save_memory(text, direct)
        return

    save_failed(text)
    speak(f"Sorry boss, my brain could not process that.")


def main():
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║     VICTUS AI - FINAL JARVIS v5.0        ║")
    print("  ║     Your Personal AI Operating System     ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    # ── Init ──
    init_brain()

    # Vision loads in background (heavy, ~1GB first time)
    import threading
    threading.Thread(target=init_vision, daemon=True).start()

    # ── Boot ──
    boot_beep()
    brain_msg = f"{len(AVAILABLE)} AI models" if AVAILABLE else "Brain offline"
    speak(f"Victus AI final system online. {brain_msg}. Say Victus.")

    print()
    print("  Commands:")
    print("    'Victus open chrome'      → app control")
    print("    'Victus optimize ram'     → clear RAM")
    print("    'Victus volume up'        → volume control")
    print("    'Victus create excel'     → Excel automation")
    print("    'Victus analyze image'    → image analysis")
    print("    'Victus what is AI'       → smart AI answer")
    print("    'Victus how are you'      → system status")
    print()

    while True:
        try:
            heard = listen_passive()
            if not heard:
                continue

            if is_wake(heard):
                command = extract_after_wake(heard)

                if command:
                    beep()
                    speak("Yes boss!")
                    command = clean(command)
                    process(command)
                else:
                    beep()
                    speak("Yes boss?")
                    command = listen(timeout=7, phrase_limit=10)
                    if command:
                        command = clean(command)
                        process(command)
                    else:
                        speak("I didn't catch that.")

        except KeyboardInterrupt:
            speak("Goodbye boss.")
            break
        except Exception as e:
            print(f"[!] {e}")
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