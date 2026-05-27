"""
Victus AI - RAM Manager Module
Clears Windows Standby List cache using pure Python (no .exe needed).
Bitdefender-safe alternative to ISLC.
"""
import ctypes
from ctypes import wintypes

# ── Windows API Constants ──
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]


def enable_privilege(privilege_name):
    """Enable a Windows privilege for the current process."""
    hToken = wintypes.HANDLE()
    if not ctypes.windll.advapi32.OpenProcessToken(
        ctypes.windll.kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(hToken)
    ):
        return False

    luid = LUID()
    if not ctypes.windll.advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
        return False

    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

    if not ctypes.windll.advapi32.AdjustTokenPrivileges(
        hToken, False, ctypes.byref(tp), ctypes.sizeof(TOKEN_PRIVILEGES), None, None
    ):
        return False
    return True


def clear_standby_list():
    """Clears the Windows Standby List (cached RAM) via NT kernel API."""
    if not enable_privilege("SeProfileSingleProcessPrivilege"):
        print("[!] Failed to get privilege. Run as Administrator.")
        return False

    ntdll = ctypes.WinDLL('ntdll')
    SYSTEM_MEMORY_LIST_INFO = 0x50
    MEMORY_PURGE_STANDBY = 4

    command = ctypes.c_int(MEMORY_PURGE_STANDBY)
    status = ntdll.NtSetSystemInformation(
        SYSTEM_MEMORY_LIST_INFO,
        ctypes.byref(command),
        ctypes.sizeof(command)
    )

    if status == 0:
        print("[+] Standby List cleared successfully.")
        return True
    else:
        print(f"[-] Failed. NTSTATUS: {hex(status & 0xffffffff)}")
        return False


if __name__ == "__main__":
    print("=== Victus AI - RAM Manager Test ===")
    clear_standby_list()