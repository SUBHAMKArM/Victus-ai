"""
Victus AI - Offline Wake Word Engine (Vosk)
No internet needed. Listens continuously with minimal CPU.
Falls back to Google STT if Vosk model not found.
"""
import os
import json
import queue
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VOSK_MODEL_DIR = os.path.join(SCRIPT_DIR, "vosk-model")

# Try to import Vosk
HAS_VOSK = False
try:
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd
    HAS_VOSK = True
except ImportError:
    pass


def download_vosk_model():
    """Download small English-Indian Vosk model if not present."""
    if os.path.exists(VOSK_MODEL_DIR):
        return True

    print("[*] Downloading offline voice model (~40MB)...")
    try:
        import requests
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
        zip_path = os.path.join(SCRIPT_DIR, "vosk-model.zip")

        r = requests.get(url, stream=True, timeout=30)
        total = int(r.headers.get('content-length', 0))
        downloaded = 0

        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = int(downloaded / total * 100)
                    print(f"\r  [{pct}%] Downloading...", end="", flush=True)

        print("\n[*] Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Extract to temp, then rename
            z.extractall(SCRIPT_DIR)

        # Rename extracted folder
        for item in os.listdir(SCRIPT_DIR):
            if item.startswith("vosk-model-small") and os.path.isdir(os.path.join(SCRIPT_DIR, item)):
                os.rename(os.path.join(SCRIPT_DIR, item), VOSK_MODEL_DIR)
                break

        # Cleanup zip
        if os.path.exists(zip_path):
            os.remove(zip_path)

        print("[+] Offline voice model ready!")
        return True
    except Exception as e:
        print(f"[!] Model download failed: {e}")
        return False


class WakeEngine:
    """Offline wake word detection using Vosk."""

    WAKE_WORDS = ["victus", "vikas", "vectus", "victor", "vickers", "wiktos"]

    def __init__(self):
        self.use_vosk = False
        self.audio_queue = queue.Queue()

        if HAS_VOSK and download_vosk_model():
            try:
                self.model = Model(VOSK_MODEL_DIR)
                self.recognizer = KaldiRecognizer(self.model, 16000)
                self.use_vosk = True
                print("[*] Vosk offline wake engine: READY")
            except Exception as e:
                print(f"[!] Vosk init failed: {e}")

        if not self.use_vosk:
            print("[*] Using Google STT for wake detection (needs internet)")

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice stream."""
        self.audio_queue.put(bytes(indata))

    def listen_for_wake(self):
        """
        Listen continuously for wake word. Returns the full text heard.
        Uses Vosk (offline) or falls back to Google STT.
        """
        if self.use_vosk:
            return self._listen_vosk()
        else:
            return self._listen_google()

    def _listen_vosk(self):
        """Offline listening via Vosk."""
        try:
            with sd.RawInputStream(
                samplerate=16000, blocksize=4000, dtype='int16',
                channels=1, callback=self._audio_callback
            ):
                while True:
                    data = self.audio_queue.get()
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").lower()
                        if text and self._has_wake_word(text):
                            return text
                    else:
                        # Partial result - check for wake word too
                        partial = json.loads(self.recognizer.PartialResult())
                        text = partial.get("partial", "").lower()
                        if text and self._has_wake_word(text):
                            # Wait for full result
                            pass
        except Exception as e:
            print(f"[!] Vosk error: {e}")
            return ""

    def _listen_google(self):
        """Fallback: Google STT wake detection."""
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        mic = sr.Microphone()

        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                text = recognizer.recognize_google(audio).lower()
                if self._has_wake_word(text):
                    return text
            except Exception:
                pass
        return ""

    def _has_wake_word(self, text):
        return any(w in text for w in self.WAKE_WORDS)

    def extract_after_wake(self, text):
        for word in self.WAKE_WORDS:
            if word in text:
                after = text.split(word, 1)[-1].strip()
                if after:
                    return after
        return ""

    def clean_command(self, text):
        for word in self.WAKE_WORDS:
            text = text.replace(word, "")
        return text.strip()


if __name__ == "__main__":
    engine = WakeEngine()
    print("Say 'Victus'...")
    result = engine.listen_for_wake()
    print(f"Heard: {result}")