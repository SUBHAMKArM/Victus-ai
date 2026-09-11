"""
╔══════════════════════════════════════════════════╗
║  VICTUS AI - Voice Engine v6.0                   ║
║  "Hey Victus" wake phrase (Google recognizes!)    ║
║  NO barge-in (was causing voice echo mixing)      ║
║  show_all=True for best wake word detection       ║
║  3-Tier TTS: gTTS → pyttsx3 → SAPI              ║
╚══════════════════════════════════════════════════╝
"""
import speech_recognition as sr
import subprocess
import winsound
import time
import threading
import os
import tempfile
from difflib import SequenceMatcher
from config import (WAKE_VARIANTS_EXACT, WAKE_PHRASES, WAKE_FUZZY_THRESHOLD,
                    WAKE_BLACKLIST)
from hud import set_hud_status


# ══════════════════════════════════════════════════
#  OPTIONAL IMPORTS
# ══════════════════════════════════════════════════

HAS_WIN32 = False
try:
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    pass

HAS_GTTS = False
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    pass

HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    pass

HAS_PYTTSX3 = False
_pyttsx3_engine = None
try:
    import pyttsx3
    _pyttsx3_engine = pyttsx3.init()
    _pyttsx3_engine.setProperty('rate', 165)
    _pyttsx3_engine.setProperty('volume', 1.0)
    HAS_PYTTSX3 = True
except Exception:
    pass


# ══════════════════════════════════════════════════
#  INTERNET CHECK (cached — once every 10s)
# ══════════════════════════════════════════════════

_last_online_check = 0
_cached_online = False


def _is_online():
    global _last_online_check, _cached_online
    now = time.time()
    if now - _last_online_check < 10:
        return _cached_online
    try:
        import socket
        socket.setdefaulttimeout(2)
        socket.create_connection(("8.8.8.8", 53))
        _cached_online = True
    except OSError:
        _cached_online = False
    _last_online_check = now
    return _cached_online


# ══════════════════════════════════════════════════
#  LANGUAGE SESSION MANAGER
# ══════════════════════════════════════════════════

LANG_STT = {"en": "en-IN", "hi": "hi-IN", "bn": "bn-IN"}
LANG_TTS_GTTS = {"en": "en", "hi": "hi", "bn": "bn"}
ALL_STT = ["en-IN", "hi-IN", "bn-IN"]

WAKE_PHONETIC_BN = ["ভিক্টাস", "ভিকটাস", "হে ভিক্টাস"]
WAKE_PHONETIC_HI = ["विक्टस", "विक्टास", "हे विक्टस"]

_lang_lock = threading.Lock()
_current_lang = "en"
_mismatch_count = 0
_MISMATCH_THRESHOLD = 3


def get_current_lang():
    with _lang_lock:
        return _current_lang


def _set_lang(new_lang):
    global _current_lang, _mismatch_count
    with _lang_lock:
        _current_lang = new_lang
        _mismatch_count = 0


def _detect_language_by_script(text):
    if not text:
        return "en"
    bengali_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    if bengali_chars > 0 and bengali_chars >= hindi_chars:
        return "bn"
    if hindi_chars > 0:
        return "hi"
    try:
        from langdetect import detect
        detected = detect(text)
        if detected == "hi":
            return "hi"
        if detected == "bn":
            return "bn"
    except Exception:
        pass
    return "en"


def _update_lang_session(detected_lang):
    global _current_lang, _mismatch_count
    with _lang_lock:
        if detected_lang == _current_lang:
            _mismatch_count = 0
            return False
        _mismatch_count += 1
        print(f"  [LANG] Mismatch {_mismatch_count}/{_MISMATCH_THRESHOLD} "
              f"| locked={_current_lang} detected={detected_lang}")
        if _mismatch_count >= _MISMATCH_THRESHOLD:
            old = _current_lang
            _current_lang = detected_lang
            _mismatch_count = 0
            print(f"  [LANG] ✓ Switched: {old} → {detected_lang}")
            return True
    return False


# ══════════════════════════════════════════════════
#  MIC SETUP — IMPROVED CALIBRATION
# ══════════════════════════════════════════════════

recognizer = sr.Recognizer()
recognizer.energy_threshold = 400
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15
recognizer.dynamic_energy_ratio = 1.5
recognizer.pause_threshold = 1.0
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5
mic = sr.Microphone()

print("[*] Calibrating mic (2 seconds, stay quiet)...")
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=2)
print(f"[*] Mic ready. Energy threshold: {recognizer.energy_threshold:.0f}")


# ══════════════════════════════════════════════════
#  TTS SETUP
# ══════════════════════════════════════════════════

_sapi_speaker = None
if HAS_WIN32:
    _sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")

tts_report = []
tts_report.append("SAPI✅" if HAS_WIN32 else "SAPI❌")
tts_report.append("gTTS✅" if HAS_GTTS else "gTTS❌")
tts_report.append("pyttsx3✅" if HAS_PYTTSX3 else "pyttsx3❌")
print(f"[*] TTS engines: {' | '.join(tts_report)}")

listening = True


# ══════════════════════════════════════════════════
#  SPEAK — Simple blocking (NO barge-in)
#  Barge-in was causing echo: mic hears AI voice → chaos
# ══════════════════════════════════════════════════

def speak(text, emotion="neutral"):
    global listening
    listening = False
    set_hud_status("SPEAKING")
    lang = get_current_lang()
    print(f"  AI [{lang.upper()}] > {text}")

    try:
        if lang == "en":
            _speak_english(text, emotion)
        else:
            if HAS_GTTS and _is_online():
                ok = _speak_gtts(text, lang)
                if not ok:
                    _speak_pyttsx3_or_sapi(text, emotion)
            elif HAS_PYTTSX3:
                _speak_pyttsx3(text)
            else:
                _speak_english(text, emotion)
    finally:
        time.sleep(0.2)
        set_hud_status("LISTENING")
        listening = True


def _speak_english(text, emotion="neutral"):
    if HAS_WIN32 and _sapi_speaker:
        rate_map = {"happy": 2, "sad": -2, "angry": 1, "neutral": 0}
        try:
            _sapi_speaker.Rate = rate_map.get(emotion, 0)
            _sapi_speaker.Speak(text)
            return
        except Exception as e:
            print(f"  [!] SAPI error: {e}")
    _speak_powershell(text)


def _speak_gtts(text, lang_code):
    tmp_path = None
    try:
        tts = gTTS(text=text, lang=LANG_TTS_GTTS.get(lang_code, "en"), slow=False)
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        tts.save(tmp_path)
        if HAS_PYGAME:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
        else:
            subprocess.run(["cmd", "/c", "start", "/wait", "", tmp_path], timeout=60)
        return True
    except Exception as e:
        print(f"  [!] gTTS error: {e}")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _speak_pyttsx3(text):
    if not HAS_PYTTSX3 or _pyttsx3_engine is None:
        _speak_powershell(text)
        return
    try:
        _pyttsx3_engine.say(text)
        _pyttsx3_engine.runAndWait()
    except Exception as e:
        print(f"  [!] pyttsx3 error: {e}")
        _speak_powershell(text)


def _speak_pyttsx3_or_sapi(text, emotion="neutral"):
    if HAS_PYTTSX3:
        _speak_pyttsx3(text)
    else:
        _speak_english(text, emotion)


def _speak_powershell(text):
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


# ══════════════════════════════════════════════════
#  GOOGLE STT — GET ALL ALTERNATIVES
# ══════════════════════════════════════════════════

def _google_all_alternatives(audio, language="en-IN"):
    """
    Get ALL alternative transcriptions from Google STT.
    Returns list of strings (best first), or empty list.
    """
    try:
        result = recognizer.recognize_google(audio, language=language, show_all=True)
        if not result:
            return []

        alternatives = []
        if isinstance(result, dict):
            for alt in result.get("alternative", []):
                transcript = alt.get("transcript", "")
                if transcript:
                    alternatives.append(transcript)
        elif isinstance(result, str):
            alternatives = [result]

        return alternatives
    except (sr.UnknownValueError, sr.RequestError):
        return []
    except Exception:
        return []


def _best_transcription(audio, language="en-IN"):
    try:
        text = recognizer.recognize_google(audio, language=language)
        return text if text else ""
    except (sr.UnknownValueError, sr.RequestError):
        return ""
    except Exception:
        return ""


# ══════════════════════════════════════════════════
#  LISTEN — HIGH ACCURACY
# ══════════════════════════════════════════════════

def listen(timeout=5, phrase_limit=8):
    if not listening:
        return ""

    set_hud_status("LISTENING")
    for attempt in range(2):
        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                locked_stt = LANG_STT.get(get_current_lang(), "en-IN")

                text = _best_transcription(audio, locked_stt)
                if text:
                    print(f"  YOU [{get_current_lang().upper()}] > {text}")
                    detected = _detect_language_by_script(text)
                    _update_lang_session(detected)
                    return text.lower()

                for stt_code in ALL_STT:
                    if stt_code == locked_stt:
                        continue
                    text = _best_transcription(audio, stt_code)
                    if text:
                        lang_key = [k for k, v in LANG_STT.items() if v == stt_code][0]
                        print(f"  YOU [{lang_key.upper()} fallback] > {text}")
                        detected = _detect_language_by_script(text)
                        _update_lang_session(detected)
                        return text.lower()

                if attempt == 0:
                    continue
                return ""

            except sr.WaitTimeoutError:
                return ""
            except Exception as e:
                print(f"[!] Listen error: {e}")
                return ""
    return ""


def listen_passive():
    """
    Wake word listener.
    Uses show_all=True to check ALL Google alternatives.
    """
    set_hud_status("LISTENING")
    with mic as source:
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=6)

            # ── Get ALL alternatives from Google (English) ──
            all_alts = _google_all_alternatives(audio, "en-IN")

            if all_alts:
                # Check EVERY alternative for wake word
                for alt_text in all_alts:
                    if is_wake(alt_text):
                        best = all_alts[0]
                        print(f"  YOU > {best}")
                        if alt_text.lower() != best.lower():
                            print(f"  [WAKE] Found in alt: '{alt_text}'")
                        return best.lower()

                # No wake word in any alternative
                best = all_alts[0]
                print(f"  YOU > {best}")
                return best.lower()

            # ── English failed — try Bengali ──
            text = _best_transcription(audio, "bn-IN")
            if text:
                print(f"  YOU [BN] > {text}")
                _set_lang("bn")
                return text.lower()

            # ── Try Hindi ──
            text = _best_transcription(audio, "hi-IN")
            if text:
                print(f"  YOU [HI] > {text}")
                _set_lang("hi")
                return text.lower()

            return ""

        except sr.WaitTimeoutError:
            return ""
        except sr.RequestError:
            print("[!] No internet.")
            return ""
        except Exception as e:
            print(f"[!] Passive listen error: {e}")
            return ""


# ══════════════════════════════════════════════════
#  SMART WAKE WORD DETECTION
#  3 layers: phrase → exact → fuzzy (v-start only)
# ══════════════════════════════════════════════════

_BLACKLIST_SET = set(w.lower() for w in WAKE_BLACKLIST)


def _fuzzy_score(word):
    return SequenceMatcher(None, word.lower(), "victus").ratio()


def _find_wake_word(text):
    """
    Find wake word in text. 3-layer detection:
      1. Phrase match: "hey victus", "hp victus", "ok victus"
      2. Exact match: "victus", "vectus", "vikas", etc.
      3. Fuzzy match: starts with 'v' + score ≥ 0.55 + not blacklisted
    """
    t = text.lower()

    # ── Layer 1: Phrase match (most reliable with Google) ──
    for phrase in WAKE_PHRASES:
        if phrase in t:
            print(f"  [WAKE] Phrase match: '{phrase}'")
            return phrase, t.index(phrase)

    # ── Layer 2: Exact word match ──
    words = t.split()
    for i, word in enumerate(words):
        if word in WAKE_VARIANTS_EXACT:
            return word, i

    # ── Layer 3: Fuzzy match (must start with 'v', not blacklisted) ──
    for i, word in enumerate(words):
        if len(word) < 4:
            continue
        if word in _BLACKLIST_SET:
            continue
        if not word.startswith('v'):
            continue
        score = _fuzzy_score(word)
        if score >= WAKE_FUZZY_THRESHOLD:
            print(f"  [WAKE] Fuzzy: '{word}' → {score:.2f}")
            return word, i

    # ── Layer 4: Bengali/Hindi phonetic ──
    for w in WAKE_PHONETIC_BN + WAKE_PHONETIC_HI:
        if w in text:
            return w, 0

    return None, -1


def is_wake(text):
    word, _ = _find_wake_word(text)
    return word is not None


def extract_after_wake(text):
    word, pos = _find_wake_word(text)
    if word is None:
        return ""

    t = text.lower()
    if word.lower() in t:
        after = t.split(word.lower(), 1)[-1].strip()
        if after:
            return after

    if word in text:
        after = text.split(word, 1)[-1].strip()
        if after:
            return after.lower()

    return ""


def clean(text):
    result = text.lower()
    # Remove phrase matches first
    for phrase in WAKE_PHRASES:
        result = result.replace(phrase, "")
    # Then single word matches
    word, _ = _find_wake_word(result)
    if word:
        result = result.replace(word.lower(), "")
    for w in WAKE_PHONETIC_BN + WAKE_PHONETIC_HI:
        result = result.replace(w, "")
    return result.strip()


# ══════════════════════════════════════════════════
#  UTILS
# ══════════════════════════════════════════════════

def beep():
    try:
        winsound.Beep(1000, 200)
    except Exception:
        pass


def boot_beep():
    try:
        winsound.Beep(800, 150)
        winsound.Beep(1000, 150)
        winsound.Beep(1200, 200)
    except Exception:
        pass
