from __future__ import annotations

import tkinter as tk
from tkinter import ttk

THEMES: dict[str, dict[str, str]] = {
    "aurora": {
        "bg": "#0f172a",
        "surface": "#111c44",
        "card": "#172554",
        "card_alt": "#1d4ed8",
        "accent": "#22c55e",
        "accent_alt": "#38bdf8",
        "text": "#e2e8f0",
        "muted": "#93c5fd",
        "danger": "#fb7185",
        "button_text": "#082f1b",
        "danger_text": "#4c0519",
    },
    "sunset": {
        "bg": "#1c1917",
        "surface": "#292524",
        "card": "#7c2d12",
        "card_alt": "#c2410c",
        "accent": "#f59e0b",
        "accent_alt": "#fb7185",
        "text": "#ffedd5",
        "muted": "#fdba74",
        "danger": "#ef4444",
        "button_text": "#431407",
        "danger_text": "#fee2e2",
    },
    "forest": {
        "bg": "#052e16",
        "surface": "#14532d",
        "card": "#166534",
        "card_alt": "#0f766e",
        "accent": "#84cc16",
        "accent_alt": "#2dd4bf",
        "text": "#ecfccb",
        "muted": "#a7f3d0",
        "danger": "#fb7185",
        "button_text": "#1a2e05",
        "danger_text": "#4c0519",
    },
}


def get_theme_names() -> list[str]:
    return list(THEMES.keys())


def get_palette(theme_name: str) -> dict[str, str]:
    return THEMES.get(theme_name, THEMES["aurora"])


def apply_theme(root: tk.Tk, theme_name: str) -> tuple[ttk.Style, dict[str, str]]:
    palette = get_palette(theme_name)
    root.configure(bg=palette["bg"])
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("App.TFrame", background=palette["bg"])
    style.configure("Card.TLabelframe", background=palette["surface"], foreground=palette["text"], borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=palette["surface"], foreground=palette["muted"], font=("Segoe UI", 10, "bold"))
    style.configure("Title.TLabel", background=palette["bg"], foreground=palette["text"], font=("Segoe UI", 16, "bold"))
    style.configure("Subtitle.TLabel", background=palette["bg"], foreground=palette["muted"], font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=palette["surface"], foreground=palette["text"], font=("Segoe UI", 10))
    style.configure("Status.TLabel", background=palette["surface"], foreground=palette["accent_alt"], font=("Segoe UI", 10, "bold"))
    style.configure("Accent.TButton", background=palette["accent"], foreground=palette["button_text"], font=("Segoe UI", 10, "bold"), padding=8)
    style.map("Accent.TButton", background=[("active", palette["accent_alt"]), ("disabled", "#3f3f46")], foreground=[("disabled", "#a1a1aa")])
    style.configure("Secondary.TButton", background=palette["card_alt"], foreground=palette["text"], font=("Segoe UI", 10, "bold"), padding=8)
    style.map("Secondary.TButton", background=[("active", palette["accent_alt"]), ("disabled", "#3f3f46")], foreground=[("disabled", "#a1a1aa")])
    style.configure("Danger.TButton", background=palette["danger"], foreground=palette["danger_text"], font=("Segoe UI", 10, "bold"), padding=8)
    style.map("Danger.TButton", background=[("active", "#f43f5e"), ("disabled", "#3f3f46")], foreground=[("disabled", "#a1a1aa")])
    style.configure("App.Horizontal.TScale", background=palette["surface"], troughcolor=palette["card"], sliderthickness=18)
    style.configure("App.TCombobox", fieldbackground=palette["card"], background=palette["card"], foreground=palette["text"], arrowcolor=palette["text"])
    style.configure("App.TSpinbox", fieldbackground=palette["card"], background=palette["card"], foreground=palette["text"], arrowsize=14)
    style.configure("App.TEntry", fieldbackground=palette["card"], foreground=palette["text"])

    return style, palette
