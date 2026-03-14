from __future__ import annotations

from pathlib import Path


def _start_menu_dirs() -> list[Path]:
    paths = [
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
    ]
    return [path for path in paths if path.exists()]


def discover_installed_apps(limit: int = 300) -> list[tuple[str, str]]:
    items: dict[str, str] = {}

    for base in _start_menu_dirs():
        for ext in ("*.lnk", "*.appref-ms", "*.url", "*.exe"):
            for file in base.rglob(ext):
                name = file.stem.strip()
                if len(name) < 2:
                    continue
                # Aynı isimleri tekilleştiriyoruz.
                items.setdefault(name, str(file))
                if len(items) >= limit:
                    break
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break

    sorted_items = sorted(items.items(), key=lambda pair: pair[0].casefold())
    return sorted_items
