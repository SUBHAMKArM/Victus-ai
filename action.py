"""Victus AI - System Actions"""
import os
import subprocess
import shutil
import psutil

# ── Volume ──
HAS_VOLUME = False
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_VOLUME = True
except ImportError:
    pass

# ── Brightness ──
HAS_BRIGHTNESS = False
try:
    import screen_brightness_control as sbc
    HAS_BRIGHTNESS = True
except ImportError:
    pass

# ── App map ──
APPS = {
    "chrome": "start chrome", "google": "start chrome",
    "edge": "start msedge", "firefox": "start firefox",
    "notepad": "start notepad", "calculator": "start calc",
    "explorer": "start explorer", "files": "start explorer",
    "settings": "start ms-settings:", "control panel": "start control",
    "task manager": "start taskmgr",
    "terminal": "start wt", "cmd": "start cmd",
    "command prompt": "start cmd", "powershell": "start powershell",
    "word": "start winword", "excel": "start excel",
    "powerpoint": "start powerpnt",
    "discord": "start discord", "teams": "start msteams:",
    "spotify": "start spotify:",
    "vs code": "start code", "vscode": "start code",
    "youtube": "start https://youtube.com",
    "whatsapp": "start whatsapp:",
}

import re
def extract_number(text):
    nums = re.findall(r'\d+', text)
    return int(nums[0]) if nums else None


def handle_command(text):
    """Try to handle as system command. Returns (handled, response)."""

    # ── Open app ──
    if "open" in text:
        app = text.split("open", 1)[-1].strip()
        cmd = APPS.get(app, f"start {app}")
        subprocess.Popen(cmd, shell=True)
        return True, f"Opening {app}"

    # ── Close app ──
    elif "close" in text:
        app = text.split("close", 1)[-1].strip()
        killed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app in proc.info['name'].lower():
                    psutil.Process(proc.info['pid']).terminate()
                    killed += 1
            except Exception:
                pass
        if killed:
            return True, f"Closed {killed} {app} processes"
        return True, f"No {app} found running"

    # ── Volume ──
    elif "volume up" in text or "louder" in text:
        return True, set_volume_relative(20)
    elif "volume down" in text or "quieter" in text:
        return True, set_volume_relative(-20)
    elif "mute" in text:
        return True, set_volume(0)
    elif "volume" in text:
        num = extract_number(text)
        if num is not None:
            return True, set_volume(num)
        vol = get_volume()
        return True, f"Volume is {vol} percent" if vol >= 0 else "Cannot read volume"

    # ── Brightness ──
    elif "brightness up" in text or "brighter" in text:
        return True, set_brightness_relative(20)
    elif "brightness down" in text or "dimmer" in text or "dim" in text:
        return True, set_brightness_relative(-20)
    elif "brightness" in text:
        num = extract_number(text)
        if num is not None:
            return True, set_brightness(num)
        brt = get_brightness()
        return True, f"Brightness is {brt} percent" if brt >= 0 else "Cannot read brightness"

    # ── RAM ──
    elif any(w in text for w in ["optimize", "clear ram", "fix ram", "clean ram", "clean memory"]):
        from ram_manager import clear_standby_list
        ok = clear_standby_list()
        mem = psutil.virtual_memory()
        if ok:
            return True, f"RAM cleared. {mem.available / (2**30):.1f} GB free"
        return True, "Failed. Need Administrator"

    # ── Storage ──
    elif any(w in text for w in ["storage", "disk", "space", "drive"]):
        total, used, free = shutil.disk_usage("C:\\")
        return True, f"C drive has {free / (2**30):.1f} GB free out of {total / (2**30):.1f} GB"

    # ── Power ──
    elif any(w in text for w in ["shut down", "shutdown", "power off"]):
        os.system("shutdown /s /t 5")
        return True, "Shutting down in 5 seconds"
    elif any(w in text for w in ["restart", "reboot"]):
        os.system("shutdown /r /t 5")
        return True, "Restarting in 5 seconds"
    elif "sleep" in text:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return True, "Going to sleep"
    elif "lock" in text:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True, "Locked"

    # ── System status ──
    elif any(w in text for w in ["status", "how are you", "system", "health"]):
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        vol = get_volume()
        r = f"All good boss. CPU {cpu:.0f} percent. RAM {mem.percent} percent"
        if vol >= 0:
            r += f". Volume {vol} percent"
        return True, r

    # ── Time / Date ──
    elif "time" in text:
        import time
        return True, f"It is {time.strftime('%I:%M %p')}"
    elif "date" in text or "today" in text:
        import time
        return True, f"Today is {time.strftime('%A, %B %d, %Y')}"

    # ── Identity ──
    elif any(w in text for w in ["your name", "who are you", "what are you"]):
        return True, "I am Victus AI. Your personal Jarvis."

    # ── Not a system command ──
    return False, ""


# ── Volume helpers ──
def get_volume():
    if not HAS_VOLUME: return -1
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return int(volume.GetMasterVolumeLevelScalar() * 100)
    except: return -1

def set_volume(level):
    if not HAS_VOLUME: return "Volume control unavailable"
    try:
        level = max(0, min(100, int(level)))
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level} percent"
    except Exception as e: return f"Volume error: {e}"

def set_volume_relative(delta):
    current = get_volume()
    if current < 0: return "Cannot read volume"
    return set_volume(current + delta)

# ── Brightness helpers ──
def get_brightness():
    if not HAS_BRIGHTNESS: return -1
    try: return sbc.get_brightness()[0]
    except: return -1

def set_brightness(level):
    if not HAS_BRIGHTNESS: return "Brightness control unavailable"
    try:
        sbc.set_brightness(max(0, min(100, int(level))))
        return f"Brightness set to {level} percent"
    except Exception as e: return f"Brightness error: {e}"

def set_brightness_relative(delta):
    current = get_brightness()
    if current < 0: return "Cannot read brightness"
    return set_brightness(current + delta)