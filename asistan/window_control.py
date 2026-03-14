from __future__ import annotations

import ctypes
import subprocess
import unicodedata
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SW_RESTORE = 9
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_SHOW = 5


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _normalize(value: str) -> str:
    lowered = value.casefold().strip()
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value.strip()


def _get_pid(hwnd: int) -> int:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def _process_name_for_pid(pid: int) -> str:
    if pid <= 0:
        return ""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        line = (result.stdout or "").strip().splitlines()
        if not line:
            return ""
        raw = line[0].strip().strip('"')
        parts = [item.strip('"') for item in raw.split('","')]
        if not parts:
            return ""
        return parts[0].replace(".exe", "")
    except Exception:
        return ""


def _list_windows() -> list[dict[str, str | int]]:
    windows: list[dict[str, str | int]] = []

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _get_window_text(hwnd)
        if not title:
            return True
        pid = _get_pid(hwnd)
        windows.append(
            {
                "hwnd": int(hwnd),
                "title": title,
                "title_norm": _normalize(title),
                "pid": pid,
                "process": _process_name_for_pid(pid),
                "process_norm": _normalize(_process_name_for_pid(pid)),
            }
        )
        return True

    user32.EnumWindows(callback, 0)
    return windows


def _find_window(target: str) -> dict[str, str | int] | None:
    needle = _normalize(target)
    if not needle:
        return None

    windows = _list_windows()

    for window in windows:
        if needle == window["process_norm"] or needle == window["title_norm"]:
            return window

    for window in windows:
        if needle in str(window["process_norm"]) or needle in str(window["title_norm"]):
            return window

    return None


def _move_window(hwnd: int, left: int, top: int, width: int, height: int) -> None:
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.MoveWindow(hwnd, left, top, width, height, True)
    user32.SetForegroundWindow(hwnd)


def control_window(action: str, target: str) -> tuple[bool, str]:
    window = _find_window(target)
    if window is None:
        return False, f"Pencere bulunamadi: {target}"

    hwnd = int(window["hwnd"])
    title = str(window["title"])

    if action == "one_getir":
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True, f"Pencere one getirildi: {title}"

    if action == "kucult":
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        return True, f"Pencere kucultuldu: {title}"

    if action == "buyut":
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        user32.SetForegroundWindow(hwnd)
        return True, f"Pencere buyutuldu: {title}"

    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    half_width = max(320, screen_width // 2)

    if action == "sola_yasla":
        _move_window(hwnd, 0, 0, half_width, screen_height)
        return True, f"Pencere sola yaslandi: {title}"

    if action == "saga_yasla":
        _move_window(hwnd, screen_width - half_width, 0, half_width, screen_height)
        return True, f"Pencere saga yaslandi: {title}"

    return False, f"Desteklenmeyen pencere eylemi: {action}"


def control_active_window(action: str) -> tuple[bool, str]:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False, "Aktif pencere bulunamadi"

    title = _get_window_text(hwnd) or "aktif pencere"

    if action == "kucult":
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        return True, f"Aktif pencere kucultuldu: {title}"

    if action == "buyut":
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        return True, f"Aktif pencere buyutuldu: {title}"

    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    half_width = max(320, screen_width // 2)

    if action == "sola_yasla":
        _move_window(hwnd, 0, 0, half_width, screen_height)
        return True, f"Aktif pencere sola yaslandi: {title}"

    if action == "saga_yasla":
        _move_window(hwnd, screen_width - half_width, 0, half_width, screen_height)
        return True, f"Aktif pencere saga yaslandi: {title}"

    return False, f"Desteklenmeyen aktif pencere eylemi: {action}"
