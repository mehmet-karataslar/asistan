from __future__ import annotations

from typing import Callable

import customtkinter as ctk

# (command_id, display_name, default_phrase)
WINDOW_COMMANDS: list[tuple[str, str, str]] = [
    ("aktif_pencere_kucult",     "Aktif Pencereyi Küçült",        "aktif pencereyi küçült"),
    ("aktif_pencere_buyut",      "Aktif Pencereyi Büyüt",         "aktif pencereyi büyüt"),
    ("aktif_pencere_sola_yasla", "Aktif Pencere → Sol Yarı",      "aktif pencereyi sola yasla"),
    ("aktif_pencere_saga_yasla", "Aktif Pencere → Sağ Yarı",      "aktif pencereyi sağa yasla"),
    ("tum_pencereleri_kucult",   "Tüm Pencereleri Küçült",        "tüm pencereleri küçült"),
]

_CMD_INDEX: dict[str, tuple[str, str]] = {
    cmd_id: (name, phrase) for cmd_id, name, phrase in WINDOW_COMMANDS
}

_QUICK_ACTIONS: list[tuple[str, str]] = [
    ("aktif_pencere_kucult",     "⬇ Küçült"),
    ("aktif_pencere_buyut",      "⬆ Büyüt"),
    ("aktif_pencere_sola_yasla", "⬅ Sola"),
    ("aktif_pencere_saga_yasla", "➡ Sağa"),
    ("tum_pencereleri_kucult",   "↓↓ Tümünü"),
]

_NAMED_ACTIONS: list[tuple[str, str]] = [
    ("one_getir",  "▲ Öne"),
    ("kucult",     "⬇ Küçült"),
    ("buyut",      "⬆ Büyüt"),
    ("sola_yasla", "⬅ Sola"),
    ("saga_yasla", "➡ Sağa"),
]


class PencereTab:
    """Akıllı pencere yönetimi sekmesi."""

    def __init__(
        self,
        parent,
        on_test_action: Callable[[str], None],
        on_save: Callable[[dict[str, str]], None],
        on_named_window_action: Callable[[str, str], None],
    ) -> None:
        self._on_test = on_test_action
        self._on_save = on_save
        self._on_named = on_named_window_action
        self._phrase_vars: dict[str, ctk.StringVar] = {}
        self._entry_widgets: list[ctk.CTkEntry] = []
        self._btn_widgets: list[ctk.CTkButton] = []
        self._section_cards: list[ctk.CTkFrame] = []

        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.root, text="Pencere Yönetimi", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            self.root,
            text=(
                "Aktif pencere üzerinde sesli komut veya butonlarla hızlıca işlem yapın. "
                "Tetikleyici ifadeleri özelleştirebilirsiniz."
            ),
            justify="left",
            wraplength=750,
        ).pack(anchor="w", padx=12, pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(self.root)
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self._build_phrase_section()
        self._build_quick_section()
        self._build_named_section()

        # Save bar
        bar = ctk.CTkFrame(self.root, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(4, 10))

        self._save_btn = ctk.CTkButton(bar, text="Kaydet", command=self._save, width=140)
        self._save_btn.pack(side="left", padx=(0, 8))

        reset_btn = ctk.CTkButton(bar, text="Sıfırla", command=self._reset_all, width=130)
        reset_btn.pack(side="left")
        self._btn_widgets.append(reset_btn)

        self._info_var = ctk.StringVar(value="")
        ctk.CTkLabel(bar, textvariable=self._info_var).pack(side="left", padx=12)

    # ─── Section builders ────────────────────────────────────────────────────

    def _build_phrase_section(self) -> None:
        ctk.CTkLabel(
            self._scroll, text="Tetikleyici İfadeler", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=4, pady=(8, 2))

        card = ctk.CTkFrame(self._scroll, corner_radius=10, border_width=1)
        card.pack(fill="x", padx=0, pady=(0, 8))
        self._section_cards.append(card)

        for cmd_id, display_name, default_phrase in WINDOW_COMMANDS:
            var = ctk.StringVar(value=default_phrase)
            self._phrase_vars[cmd_id] = var

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)

            ctk.CTkLabel(row, text=display_name, width=200, anchor="w").pack(side="left")

            entry = ctk.CTkEntry(row, textvariable=var, width=265)
            entry.pack(side="left", padx=(0, 4))
            self._entry_widgets.append(entry)

            reset_btn = ctk.CTkButton(
                row, text="↺", width=34,
                command=lambda cid=cmd_id, dp=default_phrase: self._phrase_vars[cid].set(dp),
            )
            reset_btn.pack(side="left", padx=(0, 4))
            self._btn_widgets.append(reset_btn)

            test_btn = ctk.CTkButton(
                row, text="▶ Test", width=80,
                command=lambda cid=cmd_id: self._on_test(cid),
            )
            test_btn.pack(side="left")
            self._btn_widgets.append(test_btn)

    def _build_quick_section(self) -> None:
        ctk.CTkLabel(
            self._scroll,
            text="Hızlı Eylemler (Aktif Pencere)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=4, pady=(12, 2))

        card = ctk.CTkFrame(self._scroll, corner_radius=10, border_width=1)
        card.pack(fill="x", padx=0, pady=(0, 8))
        self._section_cards.append(card)

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=12)

        for cmd_id, label in _QUICK_ACTIONS:
            btn = ctk.CTkButton(
                btn_row, text=label, width=120,
                command=lambda cid=cmd_id: self._on_test(cid),
            )
            btn.pack(side="left", padx=4)
            self._btn_widgets.append(btn)

    def _build_named_section(self) -> None:
        ctk.CTkLabel(
            self._scroll, text="İsimli Pencere Kontrolü", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=4, pady=(12, 2))

        card = ctk.CTkFrame(self._scroll, corner_radius=10, border_width=1)
        card.pack(fill="x", padx=0, pady=(0, 8))
        self._section_cards.append(card)

        help_lbl = ctk.CTkLabel(
            card,
            text=(
                "Sesli komut örnekleri:  "
                "\"Chrome öne getir\"  •  \"Discord'u küçült\"  •  \"Spotify'ı sola yasla\"\n"
                "Uygulama adını girerek aşağıdaki butonlarla da işlem yapabilirsiniz."
            ),
            justify="left",
            wraplength=680,
        )
        help_lbl.pack(anchor="w", padx=12, pady=(8, 6))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(row, text="Uygulama:", width=80, anchor="w").pack(side="left")

        self._named_app_var = ctk.StringVar()
        app_entry = ctk.CTkEntry(
            row, textvariable=self._named_app_var, width=190, placeholder_text="chrome, notepad..."
        )
        app_entry.pack(side="left", padx=(4, 8))
        self._entry_widgets.append(app_entry)

        for win_action, label in _NAMED_ACTIONS:
            btn = ctk.CTkButton(
                row, text=label, width=88,
                command=lambda wa=win_action: self._on_named(wa, self._named_app_var.get().strip()),
            )
            btn.pack(side="left", padx=2)
            self._btn_widgets.append(btn)

    # ─── Public API ─────────────────────────────────────────────────────────

    def load_phrases(self, phrases: dict[str, str]) -> None:
        for cmd_id, phrase in phrases.items():
            if cmd_id in self._phrase_vars and phrase.strip():
                self._phrase_vars[cmd_id].set(phrase.strip())

    def get_phrases(self) -> dict[str, str]:
        return {cid: var.get().strip() for cid, var in self._phrase_vars.items()}

    def set_info(self, text: str) -> None:
        self._info_var.set(text)

    def set_theme(self, palette: dict[str, str]) -> None:
        for card in self._section_cards:
            try:
                card.configure(fg_color=palette["surface"], border_color=palette["surface_alt"])
            except Exception:
                pass
        for entry in self._entry_widgets:
            try:
                entry.configure(
                    fg_color=palette["input"],
                    text_color=palette["text"],
                    border_color=palette["surface_alt"],
                )
            except Exception:
                pass
        for btn in self._btn_widgets:
            try:
                btn.configure(
                    fg_color=palette["surface_alt"],
                    hover_color=palette["accent"],
                    text_color=palette["text"],
                )
            except Exception:
                pass
        try:
            self._save_btn.configure(
                fg_color=palette["success"],
                hover_color=palette["success_hover"],
                text_color=palette["text"],
            )
        except Exception:
            pass

    # ─── Private ────────────────────────────────────────────────────────────

    def _save(self) -> None:
        self._on_save(self.get_phrases())
        self._info_var.set("Kaydedildi ✓")

    def _reset_all(self) -> None:
        for cmd_id, _, default_phrase in WINDOW_COMMANDS:
            if cmd_id in self._phrase_vars:
                self._phrase_vars[cmd_id].set(default_phrase)
        self._info_var.set("Sıfırlandı")
