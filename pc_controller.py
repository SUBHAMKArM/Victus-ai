"""
Victus AI - PC Controller Module
Full system control: apps, storage, RAM, volume, brightness, shutdown.
"""
import os
import shutil
import subprocess
import psutil

# ── Volume Control ──
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_VOLUME = True
except ImportError:
    HAS_VOLUME = False
    print("[!] pycaw not installed. Volume control disabled.")

# ── Brightness Control ──
try:
    import screen_brightness_control as sbc
    HAS_BRIGHTNESS = True
except ImportError:
    HAS_BRIGHTNESS = False
    print("[!] screen_brightness_control not installed. Brightness disabled.")


class PCController:

    # ── Correct Windows app names → launch commands ──
    APP_MAP = {
        # Browsers
        "chrome": "start chrome", "google": "start chrome",
        "edge": "start msedge", "firefox": "start firefox",
        "brave": "start brave",
        # System
        "notepad": "start notepad", "calculator": "start calc",
        "explorer": "start explorer", "files": "start explorer",
        "settings": "start ms-settings:", "control panel": "start control",
        "task manager": "start taskmgr",
        # Terminal
        "terminal": "start wt", "cmd": "start cmd",
        "command prompt": "start cmd", "powershell": "start powershell",
        # Office
        "word": "start winword", "excel": "start excel",
        "powerpoint": "start powerpnt",
        # Media
        "spotify": "start spotify:", "vlc": "start vlc",
        # Communication
        "discord": "start discord", "teams": "start msteams:",
        "whatsapp": "start whatsapp:",
        # Dev
        "vs code": "start code", "vscode": "start code",
    }

    def get_storage_analysis(self, drive="C:\\"):
        try:
            total, used, free = shutil.disk_usage(drive)
            total_gb = total / (2**30)
            used_gb = used / (2**30)
            free_gb = free / (2**30)
            pct = (used / total) * 100
            text = f"Your {drive} drive has {free_gb:.1f} GB free out of {total_gb:.1f} GB. {pct:.0f} percent used."
            return {"ok": True, "text": text, "free_gb": free_gb}
        except Exception as e:
            return {"ok": False, "text": f"Storage error: {e}"}

    def open_application(self, app_name):
        app_name = app_name.lower().strip()
        cmd = self.APP_MAP.get(app_name, f"start {app_name}")
        try:
            subprocess.Popen(cmd, shell=True)
            return {"ok": True, "text": f"Opening {app_name}."}
        except Exception:
            return {"ok": False, "text": f"Could not open {app_name}."}

    def close_application(self, app_name):
        app_name = app_name.lower().strip()
        killed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_name in proc.info['name'].lower():
                    psutil.Process(proc.info['pid']).terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed > 0:
            return {"ok": True, "text": f"Closed {killed} {app_name} processes."}
        return {"ok": False, "text": f"No running process named {app_name} found."}

    def get_ram_info(self):
        mem = psutil.virtual_memory()
        return {
            "total_gb": mem.total / (2**30),
            "used_gb": mem.used / (2**30),
            "free_gb": mem.available / (2**30),
            "percent": mem.percent,
        }

    def run_system_command(self, cmd):
        """Execute any system command."""
        try:
            subprocess.Popen(cmd, shell=True)
            return {"ok": True, "text": "Done."}
        except Exception as e:
            return {"ok": False, "text": f"Command failed: {e}"}

    # ── Volume ──
    def set_volume(self, level):
        """Set system volume. level = 0 to 100."""
        if not HAS_VOLUME:
            return "Volume control not available. Install pycaw."
        try:
            level = max(0, min(100, int(level)))
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level} percent."
        except Exception as e:
            return f"Volume error: {e}"

    def get_volume(self):
        if not HAS_VOLUME:
            return -1
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            return int(volume.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            return -1

    # ── Brightness ──
    def set_brightness(self, level):
        """Set screen brightness. level = 0 to 100."""
        if not HAS_BRIGHTNESS:
            return "Brightness control not available."
        try:
            level = max(0, min(100, int(level)))
            sbc.set_brightness(level)
            return f"Brightness set to {level} percent."
        except Exception as e:
            return f"Brightness error: {e}"

    def get_brightness(self):
        if not HAS_BRIGHTNESS:
            return -1
        try:
            return sbc.get_brightness()[0]
        except Exception:
            return -1

    # ── System Power ──
    def shutdown_pc(self, delay=5):
        os.system(f"shutdown /s /t {delay}")
        return f"PC shutting down in {delay} seconds."

    def restart_pc(self, delay=5):
        os.system(f"shutdown /r /t {delay}")
        return f"PC restarting in {delay} seconds."

    def sleep_pc(self):
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Going to sleep."

    def lock_pc(self):
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "PC locked."


if __name__ == "__main__":
    pc = PCController()
    print("Storage:", pc.get_storage_analysis()["text"])
    info = pc.get_ram_info()
    print(f"RAM: {info['used_gb']:.1f}/{info['total_gb']:.1f} GB ({info['percent']}%)")
    vol = pc.get_volume()
    if vol >= 0:
        print(f"Volume: {vol}%")
    brt = pc.get_brightness()
    if brt >= 0:
        print(f"Brightness: {brt}%")