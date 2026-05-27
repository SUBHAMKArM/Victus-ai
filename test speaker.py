"""
Quick TTS diagnostic - run this to find which method works on your system.
"""
import subprocess

print("=" * 50)
print("  TTS Diagnostic Tool")
print("=" * 50)

# ── Test 1: pyttsx3 ──
print("\n[TEST 1] pyttsx3...")
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    print(f"  Found {len(voices)} voices:")
    for i, v in enumerate(voices):
        print(f"    [{i}] {v.name}")
    engine.setProperty('voice', voices[0].id)
    engine.say("Test one. P Y T T S X 3 voice zero.")
    engine.runAndWait()
    print("  Did you hear audio? (y/n)")
except Exception as e:
    print(f"  FAILED: {e}")

input("  Press Enter to continue...\n")

# ── Test 2: pyttsx3 voice index 1 ──
print("[TEST 2] pyttsx3 voice index 1...")
try:
    engine2 = pyttsx3.init()
    engine2.setProperty('volume', 1.0)
    voices2 = engine2.getProperty('voices')
    if len(voices2) > 1:
        engine2.setProperty('voice', voices2[1].id)
        engine2.say("Test two. P Y T T S X 3 voice one.")
        engine2.runAndWait()
    else:
        print("  Only 1 voice available, skipping.")
    print("  Did you hear audio? (y/n)")
except Exception as e:
    print(f"  FAILED: {e}")

input("  Press Enter to continue...\n")

# ── Test 3: PowerShell SAPI (completely different engine) ──
print("[TEST 3] PowerShell SAPI (Windows built-in)...")
try:
    cmd = 'powershell -Command "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak(\'Test three. PowerShell voice working.\')"'
    subprocess.run(cmd, shell=True, timeout=10)
    print("  Did you hear audio? (y/n)")
except Exception as e:
    print(f"  FAILED: {e}")

input("  Press Enter to continue...\n")

# ── Test 4: Windows Media Player beep ──
print("[TEST 4] Beep sound...")
try:
    import winsound
    winsound.Beep(1000, 500)
    print("  Did you hear a beep? (y/n)")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n" + "=" * 50)
print("DONE. Tell me which test(s) produced audio!")
print("=" * 50)
input("Press Enter to exit...")