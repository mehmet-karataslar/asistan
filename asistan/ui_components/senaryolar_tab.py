from __future__ import annotations

from typing import Callable

import customtkinter as ctk

# ─── Action catalogue ────────────────────────────────────────────────────────
# (action_id, display_name, needs_value)
STEP_ACTIONS: list[tuple[str, str, bool]] = [
    ("sesi_ac",               "Ses Yükselt",                True),
    ("sesi_kis",              "Ses Kıs",                    True),
    ("sesi_sessize_al",       "Sessiz Yap",                 False),
    ("parlaklik_arttir",      "Parlaklık Artır",            True),
    ("parlaklik_azalt",       "Parlaklık Azalt",            True),
    ("ekrani_kilitle",        "Ekranı Kilitle",             False),
    ("ekran_goruntusu",       "Ekran Görüntüsü Al",         False),
    ("cop_kutusu_ac",         "Çöp Kutusunu Aç",            False),
    ("wifi_ac",               "WiFi Aç",                    False),
    ("wifi_kapat",            "WiFi Kapat",                 False),
    ("bluetooth_ac",          "Bluetooth Aç",               False),
    ("bluetooth_kapat",       "Bluetooth Kapat",            False),
    ("tum_pencereleri_kucult","Tüm Pencereleri Küçült",     False),
]

_ACTION_DISPLAY:    dict[str, str]  = {a: d          for a, d, _ in STEP_ACTIONS}
_ACTION_NEEDS_VAL:  dict[str, bool] = {a: n          for a, _, n in STEP_ACTIONS}
_DISPLAY_TO_ACTION: dict[str, str]  = {d: a          for a, d, _ in STEP_ACTIONS}
_ACTION_DISPLAYS:   list[str]       = [d             for _, d, _ in STEP_ACTIONS]

_DEFAULT_VALUE: dict[str, str] = {
    "sesi_ac":          "6",
    "sesi_kis":         "6",
    "parlaklik_arttir": "15",
    "parlaklik_azalt":  "15",
}


class SenaryolarTab:
    """Çok adımlı senaryo yönetimi sekmesi."""

    def __init__(
        self,
        parent,
        on_save: Callable[[list[dict]], None],
        on_test_scenario: Callable[[str], None],
    ) -> None:
        self._on_save = on_save
        self._on_test = on_test_scenario
        self._scenarios: list[dict] = []
        self._selected_idx: int = -1
        self._step_rows: list[dict] = []   # [{frame, action_var, value_var}]
        self._list_btns: list[ctk.CTkButton] = []

        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.root,
            text="Çok Adımlı Senaryolar",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            self.root,
            text=(
                "Senaryolar birden fazla eylemi sırayla çalıştırır. "
                "Mevcut senaryoları düzenleyin, yeni adımlar ekleyin veya sıfırdan senaryo oluşturun."
            ),
            justify="left",
            wraplength=800,
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # ── Two-panel layout ────────────────────────────────────────────────
        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        # ── Left: scenario list ────────────────────────────────────────────
        self._left = ctk.CTkFrame(content, corner_radius=10, border_width=1)
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            self._left, text="Senaryolar", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self._list_scroll = ctk.CTkScrollableFrame(self._left, height=300)
        self._list_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        list_btns = ctk.CTkFrame(self._left, fg_color="transparent")
        list_btns.pack(fill="x", padx=6, pady=(0, 8))

        self._add_btn = ctk.CTkButton(
            list_btns, text="+ Yeni", width=75, command=self._add_new_scenario
        )
        self._add_btn.pack(side="left", padx=(0, 3))

        self._del_btn = ctk.CTkButton(
            list_btns, text="− Sil", width=75, command=self._delete_selected
        )
        self._del_btn.pack(side="left", padx=(0, 3))

        self._test_btn = ctk.CTkButton(
            list_btns, text="▶ Test", width=75, command=self._test_selected
        )
        self._test_btn.pack(side="left")

        # ── Right: editor ──────────────────────────────────────────────────
        self._right = ctk.CTkFrame(content, corner_radius=10, border_width=1)
        self._right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(
            self._right, text="Senaryo Düzenle", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        form = ctk.CTkFrame(self._right, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(form, text="Senaryo Adı:", width=110, anchor="w").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self._name_var = ctk.StringVar()
        self._name_entry = ctk.CTkEntry(form, textvariable=self._name_var, placeholder_text="örn: Ders Modu")
        self._name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(form, text="Tetikleyici:", width=110, anchor="w").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self._phrase_var = ctk.StringVar()
        self._phrase_entry = ctk.CTkEntry(
            form, textvariable=self._phrase_var, placeholder_text="sesli tetikleyici ifade"
        )
        self._phrase_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._right, text="Adımlar:", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(4, 2))

        self._steps_scroll = ctk.CTkScrollableFrame(self._right, height=200)
        self._steps_scroll.pack(fill="x", padx=10, pady=(0, 6))

        # "Add step" row
        add_row = ctk.CTkFrame(self._right, fg_color="transparent")
        add_row.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(add_row, text="Yeni Adım:", width=90, anchor="w").pack(side="left")

        self._new_action_var = ctk.StringVar(value=_ACTION_DISPLAYS[0])
        self._new_action_menu = ctk.CTkOptionMenu(
            add_row,
            values=_ACTION_DISPLAYS,
            variable=self._new_action_var,
            command=lambda _: self._sync_new_value_state(),
            width=210,
        )
        self._new_action_menu.pack(side="left", padx=(4, 4))

        self._new_value_var = ctk.StringVar(value="")
        self._new_value_entry = ctk.CTkEntry(
            add_row, textvariable=self._new_value_var, width=62, placeholder_text="değer"
        )
        self._new_value_entry.pack(side="left", padx=(0, 4))

        ctk.CTkButton(add_row, text="+ Adım Ekle", width=110, command=self._add_step).pack(side="left")

        # Save row
        save_row = ctk.CTkFrame(self._right, fg_color="transparent")
        save_row.pack(fill="x", padx=10, pady=(2, 10))

        self._save_btn = ctk.CTkButton(
            save_row, text="Senaryo Kaydet", command=self._save_current, width=160
        )
        self._save_btn.pack(side="left")

        self._info_var = ctk.StringVar(value="")
        ctk.CTkLabel(save_row, textvariable=self._info_var).pack(side="left", padx=10)

        self._sync_new_value_state()
        self._set_editor_enabled(False)

    # ─── Public API ─────────────────────────────────────────────────────────

    def load_scenarios(self, scenarios: list[dict]) -> None:
        self._scenarios = [dict(sc) for sc in scenarios]
        self._rebuild_list()
        if self._scenarios:
            self._select(0)

    def get_scenarios(self) -> list[dict]:
        return list(self._scenarios)

    def set_info(self, text: str) -> None:
        self._info_var.set(text)

    def set_theme(self, palette: dict[str, str]) -> None:
        for panel in (self._left, self._right):
            try:
                panel.configure(fg_color=palette["surface"], border_color=palette["surface_alt"])
            except Exception:
                pass
        for w in (self._name_entry, self._phrase_entry, self._new_value_entry):
            try:
                w.configure(
                    fg_color=palette["input"],
                    text_color=palette["text"],
                    border_color=palette["surface_alt"],
                )
            except Exception:
                pass
        for btn in (self._add_btn, self._del_btn, self._test_btn):
            try:
                btn.configure(
                    fg_color=palette["accent"],
                    hover_color=palette["accent_hover"],
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
        try:
            self._new_action_menu.configure(
                fg_color=palette["surface_alt"],
                button_color=palette["accent"],
                button_hover_color=palette["accent_hover"],
                text_color=palette["text"],
            )
        except Exception:
            pass
        # Re-theme list buttons
        for btn in self._list_btns:
            try:
                btn.configure(
                    fg_color=palette["surface_alt"],
                    hover_color=palette["accent"],
                    text_color=palette["text"],
                )
            except Exception:
                pass

    # ─── List management ────────────────────────────────────────────────────

    def _rebuild_list(self) -> None:
        for child in self._list_scroll.winfo_children():
            child.destroy()
        self._list_btns.clear()

        for idx, sc in enumerate(self._scenarios):
            btn = ctk.CTkButton(
                self._list_scroll,
                text=sc.get("display_name", sc["id"]),
                anchor="w",
                command=lambda i=idx: self._select(i),
            )
            btn.pack(fill="x", pady=2, padx=2)
            self._list_btns.append(btn)

    def _select(self, idx: int) -> None:
        if not (0 <= idx < len(self._scenarios)):
            return
        self._selected_idx = idx
        sc = self._scenarios[idx]
        self._name_var.set(sc.get("display_name", ""))
        self._phrase_var.set(sc.get("trigger_phrase", ""))
        self._load_steps(sc.get("steps", []))
        self._set_editor_enabled(True)

    def _add_new_scenario(self) -> None:
        new_id = f"senaryo_{len(self._scenarios) + 1}"
        self._scenarios.append({
            "id": new_id,
            "display_name": f"Yeni Senaryo {len(self._scenarios) + 1}",
            "trigger_phrase": "",
            "steps": [],
        })
        self._rebuild_list()
        self._select(len(self._scenarios) - 1)

    def _delete_selected(self) -> None:
        if not (0 <= self._selected_idx < len(self._scenarios)):
            return
        self._scenarios.pop(self._selected_idx)
        self._selected_idx = -1
        for child in self._steps_scroll.winfo_children():
            child.destroy()
        self._step_rows.clear()
        self._name_var.set("")
        self._phrase_var.set("")
        self._rebuild_list()
        self._set_editor_enabled(False)
        if self._scenarios:
            self._select(0)

    def _test_selected(self) -> None:
        if not (0 <= self._selected_idx < len(self._scenarios)):
            return
        self._on_test(self._scenarios[self._selected_idx]["id"])

    # ─── Steps editor ───────────────────────────────────────────────────────

    def _load_steps(self, steps: list[dict]) -> None:
        for child in self._steps_scroll.winfo_children():
            child.destroy()
        self._step_rows.clear()
        for step in steps:
            self._append_step_row(step["action"], int(step.get("value", 0)))

    def _append_step_row(self, action_id: str, value: int) -> None:
        idx = len(self._step_rows)
        row = ctk.CTkFrame(self._steps_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=f"{idx + 1}.", width=26, anchor="e").pack(side="left", padx=(0, 4))

        action_var = ctk.StringVar(value=_ACTION_DISPLAY.get(action_id, action_id))
        action_menu = ctk.CTkOptionMenu(
            row, values=_ACTION_DISPLAYS, variable=action_var, width=210
        )
        action_menu.pack(side="left", padx=(0, 4))

        value_var = ctk.StringVar(value=str(value) if value else "")
        value_entry = ctk.CTkEntry(row, textvariable=value_var, width=62)
        value_entry.pack(side="left", padx=(0, 4))

        row_data: dict = {"frame": row, "action_var": action_var, "value_var": value_var}

        def _sync_val(*_, _av=action_var, _ve=value_entry, _vv=value_var, _rd=row_data):
            act = _DISPLAY_TO_ACTION.get(_av.get(), "")
            needs = _ACTION_NEEDS_VAL.get(act, False)
            _ve.configure(state="normal" if needs else "disabled")
            if needs and not _vv.get():
                _vv.set(_DEFAULT_VALUE.get(act, "10"))
            elif not needs:
                _vv.set("")

        action_var.trace_add("write", _sync_val)
        _sync_val()

        del_btn = ctk.CTkButton(
            row, text="✕", width=32,
            command=lambda rd=row_data: self._remove_step_row(rd),
        )
        del_btn.pack(side="left")

        self._step_rows.append(row_data)

    def _remove_step_row(self, row_data: dict) -> None:
        row_data["frame"].destroy()
        if row_data in self._step_rows:
            self._step_rows.remove(row_data)

    def _add_step(self) -> None:
        if self._selected_idx < 0:
            return
        action_display = self._new_action_var.get()
        action_id = _DISPLAY_TO_ACTION.get(action_display, "")
        value = 0
        if _ACTION_NEEDS_VAL.get(action_id, False):
            try:
                value = int(self._new_value_var.get().strip() or "0")
            except ValueError:
                value = 0
        self._append_step_row(action_id, value)

    def _sync_new_value_state(self) -> None:
        action_id = _DISPLAY_TO_ACTION.get(self._new_action_var.get(), "")
        needs = _ACTION_NEEDS_VAL.get(action_id, False)
        self._new_value_entry.configure(state="normal" if needs else "disabled")
        if needs and not self._new_value_var.get():
            self._new_value_var.set(_DEFAULT_VALUE.get(action_id, "10"))
        elif not needs:
            self._new_value_var.set("")

    # ─── Save ───────────────────────────────────────────────────────────────

    def _save_current(self) -> None:
        if not (0 <= self._selected_idx < len(self._scenarios)):
            return
        sc = self._scenarios[self._selected_idx]
        # Collect steps from UI
        steps: list[dict] = []
        for rd in self._step_rows:
            act_display = rd["action_var"].get()
            act_id = _DISPLAY_TO_ACTION.get(act_display, "")
            if not act_id:
                continue
            val_str = rd["value_var"].get().strip()
            try:
                val = int(val_str) if val_str else 0
            except ValueError:
                val = 0
            steps.append({"action": act_id, "value": val})

        name = self._name_var.get().strip()
        phrase = self._phrase_var.get().strip()
        sc["display_name"] = name or sc["display_name"]
        sc["trigger_phrase"] = phrase
        sc["steps"] = steps

        self._rebuild_list()
        self._on_save(self._scenarios)
        self._info_var.set("Kaydedildi ✓")

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _set_editor_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for w in (self._name_entry, self._phrase_entry, self._save_btn, self._del_btn, self._test_btn, self._new_action_menu):
            try:
                w.configure(state=state)
            except Exception:
                pass
        self._sync_new_value_state()
