"""Victus AI - Voice (Mic + Speaker)"""
import speech_recognition as sr
import subprocess
import winsound
import time
from config import WAKE_VARIANTS


# ── Try win32com SAPI first (faster), fallback to PowerShell ──
HAS_WIN32 = False
try:
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    pass

# ── Recognizer ──
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
mic = sr.Microphone()

# Calibrate once
print("[*] Calibrating mic...")
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
print("[*] Mic ready.")

# ── TTS ──
if HAS_WIN32:
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    print("[*] TTS: win32com SAPI")
else:
    speaker = None
    print("[*] TTS: PowerShell SAPI fallback")

listening = True


def speak(text, emotion="neutral"):
    """Speak text. Adjusts speed based on emotion."""
    global listening
    listening = False
    print(f"  AI > {text}")

    if HAS_WIN32 and speaker:
        try:
            rate_map = {"happy": 2, "sad": -2, "angry": 1, "neutral": 0, "normal": 0}
            speaker.Rate = rate_map.get(emotion, 0)
            speaker.Speak(text)
        except Exception as e:
            print(f"  [!] win32 TTS error: {e}")
            _speak_powershell(text)
    else:
        _speak_powershell(text)

    time.sleep(0.2)
    listening = True


def _speak_powershell(text):
    """Fallback TTS."""
    try:
        safe = text.replace("'", "''").replace('"', '').replace('\n', ' ')
        cmd = (
            'powershell -Command "'
            'Add-Type -AssemblyName System.Speech; '
            '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            f"$s.Volume = 100; $s.Speak('{safe}')"
            '"'
        )
        subprocess.run(cmd, shell=True, timeout=30)
    except Exception as e:
        print(f"  [!] PowerShell TTS error: {e}")


def listen(timeout=5, phrase_limit=8):
    """Listen via Google STT. Returns lowercase text or empty string."""
    if not listening:
        return ""

    for attempt in range(2):
        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                text = recognizer.recognize_google(audio, language="en-IN")
                print(f"  YOU > {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                if attempt == 0: continue
                return ""
            except sr.RequestError:
                print("[!] No internet.")
                return ""
            except Exception as e:
                print(f"[!] {e}")
                return ""
    return ""


def listen_passive():
    """Listen with no timeout (for wake word detection)."""
    return listen(timeout=None, phrase_limit=10)


def beep():
    try: winsound.Beep(1000, 200)
    except: pass


def boot_beep():
    try:
        winsound.Beep(800, 150)
        winsound.Beep(1000, 150)
        winsound.Beep(1200, 200)
    except: pass


def is_wake(text):
    return any(w in text for w in WAKE_VARIANTS)


def extract_after_wake(text):
    for w in WAKE_VARIANTS:
        if w in text:
            after = text.split(w, 1)[-1].strip()
            if after: return after
    return ""


def clean(text):
    for w in WAKE_VARIANTS:
        text = text.replace(w, "")
    return text.strip()