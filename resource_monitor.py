"""
Victus AI - Resource Monitor Module
Detects if the system is under heavy load (gaming) or idle.
"""
import psutil


class ResourceMonitor:
    def __init__(self, cpu_threshold=70.0, ram_threshold=85.0):
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold

    def get_load(self):
        """Get current CPU and RAM percentages."""
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory().percent
        return {"cpu": cpu, "ram": ram}

    def is_heavy_load(self):
        """Returns True if system is under heavy load (gaming/rendering)."""
        load = self.get_load()
        heavy = load["cpu"] >= self.cpu_threshold or load["ram"] >= self.ram_threshold
        return heavy, load


if __name__ == "__main__":
    mon = ResourceMonitor()
    heavy, load = mon.is_heavy_load()
    state = "HEAVY (Gaming/Rendering)" if heavy else "IDLE"
    print(f"System State: {state}")
    print(f"CPU: {load['cpu']}% | RAM: {load['ram']}%")