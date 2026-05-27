"""
Victus AI - Voice Engine v3
PowerShell SAPI TTS + Google STT for commands + Emotional speaking
"""
import speech_recognition as sr
import subprocess
import winsound
import time


class VoiceEngine:
    WAKE_WORDS = ["victus", "vikas", "vectus", "victor", "vickers", "wiktos"]

    def __init__(self):
        # ── STT for commands (not wake word — wake_engine handles that) ──
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.mic = sr.Microphone()
        self.listening = True

        print("[*] Calibrating microphone...")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[*] Microphone ready.")

    def speak(self, text, emotion="normal"):
        """Speak using Windows SAPI. Adjusts rate based on emotion."""
        self.listening = False
        print(f"  AI > {text}")

        # Emotion → speech rate
        rate_map = {"happy": 3, "sad": -1, "angry": 2, "normal": 1}
        rate = rate_map.get(emotion, 1)

        try:
            safe = text.replace("'", "''").replace('"', '').replace('\n', ' ')
            cmd = (
                'powershell -Command "'
                'Add-Type -AssemblyName System.Speech; '
                '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$s.Rate = {rate}; '
                f'$s.Volume = 100; '
                f"$s.Speak('{safe}')"
                '"'
            )
            subprocess.run(cmd, shell=True, timeout=30)
        except Exception as e:
            print(f"  [!] TTS Error: {e}")

        time.sleep(0.2)
        self.listening = True

    def listen(self, timeout=5, phrase_limit=8, language="en-IN"):
        """Listen for a command via Google STT."""
        if not self.listening:
            return ""
        for attempt in range(2):
            with self.mic as source:
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                    text = self.recognizer.recognize_google(audio, language=language)
                    print(f"  YOU > {text}")
                    return text.lower()
                except sr.WaitTimeoutError:
                    return ""
                except sr.UnknownValueError:
                    if attempt == 0:
                        continue
                    return ""
                except sr.RequestError:
                    print("[!] No internet for speech recognition.")
                    return ""
                except Exception as e:
                    print(f"[!] Listen error: {e}")
                    return ""
        return ""

    def beep(self):
        try:
            winsound.Beep(1000, 200)
        except Exception:
            pass

    def boot_beep(self):
        """Iron Man style boot sound."""
        try:
            winsound.Beep(800, 150)
            winsound.Beep(1000, 150)
            winsound.Beep(1200, 200)
        except Exception:
            pass

    def is_wake_word(self, text):
        return any(word in text for word in self.WAKE_WORDS)

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
    v = VoiceEngine()
    v.boot_beep()
    v.speak("Hello boss. Speaker test complete.", emotion="happy")