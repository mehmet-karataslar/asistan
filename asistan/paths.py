from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_FOLDER_NAME = "Asistan"


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return Path(__file__).resolve().parents[1]


def app_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base:
        root = Path(base)
    else:
        root = Path.home()
    target = root / APP_FOLDER_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def db_file_path() -> Path:
    return app_data_dir() / "asistan_data.db"


def bundled_plugins_dir() -> Path:
    return _bundle_root() / "plugins"


def user_plugins_dir() -> Path:
    target = app_data_dir() / "plugins"
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_user_plugins_seeded() -> Path:
    source = bundled_plugins_dir()
    target = user_plugins_dir()
    if source.exists():
        for plugin_file in source.glob("*.py"):
            dest = target / plugin_file.name
            if not dest.exists():
                shutil.copy2(plugin_file, dest)
    return target


def icon_ico_path() -> Path:
    return _bundle_root() / "assets" / "icons" / "asistan-icon.ico"


def icon_png_path() -> Path:
    return _bundle_root() / "assets" / "icons" / "asistan-icon-256.png"
