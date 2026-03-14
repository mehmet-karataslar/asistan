from __future__ import annotations

from typing import Callable

import customtkinter as ctk

# (command_id, display_name, default_phrase)
SYSTEM_COMMANDS: list[tuple[str, str, str]] = [
    ("sesi_ac",           "Ses Yükselt",         "sesi artır"),
    ("sesi_kis",          "Ses Kıs",              "sesi kıs"),
    ("sesi_sessize_al",   "Sessiz Yap",           "sessize al"),
    ("parlaklik_arttir",  "Parlaklık Artır",      "parlaklığı artır"),
    ("parlaklik_azalt",   "Parlaklık Azalt",      "parlaklığı azalt"),
    ("ekrani_kilitle",    "Ekranı Kilitle",       "ekranı kilitle"),
    ("ekran_goruntusu",   "Ekran Görüntüsü Al",   "ekran görüntüsü al"),
    ("cop_kutusu_ac",     "Çöp Kutusunu Aç",      "çöp kutusunu aç"),
    ("wifi_ac",           "WiFi Aç",              "wifi aç"),
    ("wifi_kapat",        "WiFi Kapat",           "wifi kapat"),
    ("bluetooth_ac",      "Bluetooth Aç",         "bluetooth aç"),
    ("bluetooth_kapat",   "Bluetooth Kapat",      "bluetooth kapat"),
]

SYSTEM_SECTIONS: list[tuple[str, list[str]]] = [
    ("Ses Kontrolleri",  ["sesi_ac", "sesi_kis", "sesi_sessize_al"]),
    ("Parlaklık",        ["parlaklik_arttir", "parlaklik_azalt"]),
    ("Hızlı Eylemler",  ["ekrani_kilitle", "ekran_goruntusu", "cop_kutusu_ac"]),
    ("Ağ Kontrolleri",  ["wifi_ac", "wifi_kapat", "bluetooth_ac", "bluetooth_kapat"]),
]

_CMD_INDEX: dict[str, tuple[str, str]] = {
    cmd_id: (name, phrase) for cmd_id, name, phrase in SYSTEM_COMMANDS
}


class SistemKontrolTab:
    """Sistem kontrol sekmesi – ses, parlaklık, ağ ve hızlı eylemler."""

    def __init__(
        self,
        parent,
        on_test_action: Callable[[str], None],
        on_save: Callable[[dict[str, str]], None],
    ) -> None:
        self._on_test = on_test_action
        self._on_save = on_save
        self._phrase_vars: dict[str, ctk.StringVar] = {}
        self._entry_widgets: list[ctk.CTkEntry] = []
        self._btn_widgets: list[ctk.CTkButton] = []
        self._section_cards: list[ctk.CTkFrame] = []

        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.root, text="Sistem Kontrolü", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            self.root,
            text=(
                "Her komutun sesli tetikleyici ifadesini özelleştirin. "
                "'Test' butonu ile anında çalıştırın. Değişiklikler 'Kaydet' ile kalıcı olur."
            ),
            justify="left",
            wraplength=750,
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Header row
        hdr = ctk.CTkFrame(self.root, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(hdr, text="Eylem", width=170, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="Tetikleyici İfade", anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(8, 0))

        self._scroll = ctk.CTkScrollableFrame(self.root)
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        for section_name, cmd_ids in SYSTEM_SECTIONS:
            self._build_section(section_name, cmd_ids)

        # Bottom save bar
        bar = ctk.CTkFrame(self.root, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(4, 10))

        self._save_btn = ctk.CTkButton(bar, text="Kaydet", command=self._save, width=140)
        self._save_btn.pack(side="left", padx=(0, 8))

        reset_btn = ctk.CTkButton(bar, text="Tümünü Sıfırla", command=self._reset_all, width=150)
        reset_btn.pack(side="left")
        self._btn_widgets.append(reset_btn)

        self._info_var = ctk.StringVar(value="")
        ctk.CTkLabel(bar, textvariable=self._info_var).pack(side="left", padx=12)

    # ─── Build helpers ──────────────────────────────────────────────────────

    def _build_section(self, section_name: str, cmd_ids: list[str]) -> None:
        ctk.CTkLabel(
            self._scroll, text=section_name, font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=4, pady=(12, 2))

        card = ctk.CTkFrame(self._scroll, corner_radius=10, border_width=1)
        card.pack(fill="x", padx=0, pady=(0, 6))
        self._section_cards.append(card)

        for cmd_id in cmd_ids:
            display_name, default_phrase = _CMD_INDEX[cmd_id]
            var = ctk.StringVar(value=default_phrase)
            self._phrase_vars[cmd_id] = var

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)

            ctk.CTkLabel(row, text=display_name, width=170, anchor="w").pack(side="left")

            entry = ctk.CTkEntry(row, textvariable=var, width=290)
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
                card.configure(
                    fg_color=palette["surface"],
                    border_color=palette["surface_alt"],
                )
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
        for cmd_id, (_, default_phrase) in _CMD_INDEX.items():
            if cmd_id in self._phrase_vars:
                self._phrase_vars[cmd_id].set(default_phrase)
        self._info_var.set("Tüm ifadeler sıfırlandı")
