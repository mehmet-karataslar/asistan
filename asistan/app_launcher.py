from __future__ import annotations

from pathlib import Path
import subprocess


APP_COMMANDS = {
    "chrome": ["cmd", "/c", "start", "", "chrome"],
    "spotify": ["cmd", "/c", "start", "", "spotify"],
    "discord": ["cmd", "/c", "start", "", "discord"],
    "telegram": ["cmd", "/c", "start", "", "telegram"],
    "notepad": ["cmd", "/c", "start", "", "notepad"],
    "hesapmakinesi": ["cmd", "/c", "start", "", "calc"],
    "calc": ["cmd", "/c", "start", "", "calc"],
}


def launch_application(app_name: str) -> tuple[bool, str]:
    raw = app_name.strip()
    key = raw.casefold()

    # Eğer kullanıcıya listelenen bir hedef dosya yolu geldiyse doğrudan onu aç.
    target_path = Path(raw)
    if target_path.exists():
        try:
            subprocess.Popen(["cmd", "/c", "start", "", str(target_path)])
            return True, f"Uygulama aciliyor: {target_path.stem}"
        except Exception as exc:
            return False, f"Uygulama acilamadi ({raw}): {exc}"

    command = APP_COMMANDS.get(key)

    try:
        if command is None:
            command = ["cmd", "/c", "start", "", raw]
        subprocess.Popen(command)
        return True, f"Uygulama aciliyor: {raw}"
    except Exception as exc:
        return False, f"Uygulama acilamadi ({raw}): {exc}"


def close_application(app_name: str) -> tuple[bool, str]:
    raw = app_name.strip()
    if not raw:
        return False, "Kapatilacak uygulama adi bos"

    names: list[str] = []

    target_path = Path(raw)
    if target_path.exists():
        names.append(target_path.stem)

    names.append(raw)
    key = raw.casefold()
    if key in APP_COMMANDS:
        command = APP_COMMANDS[key]
        if command:
            last_arg = command[-1].strip()
            if last_arg:
                names.append(last_arg)

    # Benzersiz hale getir.
    normalized: list[str] = []
    for item in names:
        cleaned = item.strip().strip('"').replace(".exe", "")
        if cleaned and cleaned.casefold() not in {n.casefold() for n in normalized}:
            normalized.append(cleaned)

    if not normalized:
        return False, f"Uygulama adi anlasilamadi: {raw}"

    for base_name in normalized:
        exe_name = f"{base_name}.exe"
        try:
            proc = subprocess.run(
                ["taskkill", "/IM", exe_name, "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                return True, f"Uygulama kapatildi: {base_name}"
        except Exception:
            continue

    return False, f"Uygulama kapatilamadi: {raw}"
