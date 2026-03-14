from __future__ import annotations

import csv
import io
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

    alias_map: dict[str, list[str]] = {
        "muzik": ["spotify", "vlc", "wmplayer", "music", "music.ui"],
        "muzik uygulamasi": ["spotify", "vlc", "wmplayer", "music", "music.ui"],
        "music": ["spotify", "vlc", "wmplayer", "music", "music.ui"],
        "tarayici": ["chrome", "msedge", "firefox", "opera"],
    }
    names.extend(alias_map.get(key, []))

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

    # 1) Once dogrudan IM ile dene
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

    # 2) Tasklist uzerinden bulup PID ile kapat (fuzzy)
    try:
        listed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        if listed.returncode == 0 and listed.stdout.strip():
            rows = list(csv.reader(io.StringIO(listed.stdout)))
            matched: list[tuple[str, str]] = []  # (image_name, pid)
            for row in rows:
                if len(row) < 2:
                    continue
                image_name = row[0].strip().strip('"')
                pid = row[1].strip().strip('"')
                image_base = image_name.casefold().replace(".exe", "")

                for candidate in normalized:
                    c = candidate.casefold()
                    if not c:
                        continue
                    if c == image_base or c in image_base or image_base in c:
                        matched.append((image_name, pid))
                        break

            for image_name, pid in matched:
                killed = subprocess.run(
                    ["taskkill", "/PID", pid, "/F"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if killed.returncode == 0:
                    return True, f"Uygulama kapatildi: {image_name}"
    except Exception:
        pass

    return False, f"Uygulama kapatilamadi: {raw}"
