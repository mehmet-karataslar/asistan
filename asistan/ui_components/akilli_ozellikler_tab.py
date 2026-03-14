from __future__ import annotations

import customtkinter as ctk


class AkilliOzelliklerTab:
    def __init__(
        self,
        parent,
        *,
        on_refresh,
        on_set_routine,
        on_reload_plugins,
    ) -> None:
        self.on_refresh = on_refresh
        self.on_set_routine = on_set_routine
        self.on_reload_plugins = on_reload_plugins
        self.routine_id_var = ctk.StringVar(value="")
        self.routine_accept_var = ctk.StringVar(value="kabul")

        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True)

        self._cards: list[ctk.CTkFrame] = []
        self._entries: list[ctk.CTkEntry] = []
        self._menus: list[ctk.CTkOptionMenu] = []
        self._buttons: list[ctk.CTkButton] = []

        self._build_ui()

    def _card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=14, border_width=1)
        self._cards.append(card)
        return card

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(self.root, text="Akilli Ozellikler", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w", padx=12, pady=(10, 4))

        desc = ctk.CTkLabel(
            self.root,
            text="Analizler, rutin onerileri ve plugin yonetimi bu sekmede.",
            justify="left",
        )
        desc.pack(anchor="w", padx=12, pady=(0, 8))

        grid = ctk.CTkFrame(self.root, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

        analytics = self._card(grid)
        analytics.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        ctk.CTkLabel(analytics, text="Analitik ve Rutin", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        rt_row = ctk.CTkFrame(analytics, fg_color="transparent")
        rt_row.pack(fill="x", padx=10, pady=(0, 8))
        self.routine_id_entry = ctk.CTkEntry(rt_row, textvariable=self.routine_id_var, placeholder_text="onerı id")
        self.routine_id_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.routine_state_menu = ctk.CTkOptionMenu(rt_row, values=["kabul", "reddet"], variable=self.routine_accept_var)
        self.routine_state_menu.pack(side="left", padx=4)
        self.apply_routine_btn = ctk.CTkButton(rt_row, text="Uygula", command=self._handle_routine_update)
        self.apply_routine_btn.pack(side="left", padx=(4, 0))
        self._entries.append(self.routine_id_entry)
        self._menus.append(self.routine_state_menu)
        self._buttons.append(self.apply_routine_btn)

        self.analytics_box = ctk.CTkTextbox(analytics, height=170)
        self.analytics_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.analytics_box.configure(state="disabled")

        plugins = self._card(grid)
        plugins.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        ctk.CTkLabel(plugins, text="Pluginler", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))
        self.reload_plugins_btn = ctk.CTkButton(plugins, text="Pluginleri Yeniden Yukle", command=self._handle_reload_plugins)
        self.reload_plugins_btn.pack(anchor="w", padx=10, pady=(0, 6))
        self._buttons.append(self.reload_plugins_btn)

        self.plugins_box = ctk.CTkTextbox(plugins, height=170)
        self.plugins_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.plugins_box.configure(state="disabled")

        actions = self._card(grid)
        actions.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 0), pady=(6, 0))
        ctk.CTkLabel(actions, text="Hizli Islemler", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))
        self.refresh_btn = ctk.CTkButton(actions, text="Tum Verileri Yenile", command=self._handle_refresh)
        self.refresh_btn.pack(anchor="w", padx=10, pady=(0, 6))
        self._buttons.append(self.refresh_btn)

        self.info_var = ctk.StringVar(value="Hazir")
        ctk.CTkLabel(actions, textvariable=self.info_var, justify="left", wraplength=420).pack(anchor="w", padx=10, pady=(2, 10))

    def set_info(self, text: str) -> None:
        self.info_var.set(text)

    def set_data(
        self,
        *,
        analytics: list[tuple[str, int, int]],
        routines: list[tuple[int, str, bool]],
        plugins: list[str],
    ) -> None:
        analytics_lines = [f"- {a}: {tot} kez, {ok} basarili" for a, tot, ok in analytics]
        if not analytics_lines:
            analytics_lines = ["Analitik kayit yok"]
        analytics_lines.append("")
        analytics_lines.append("Rutin Onerileri:")
        if routines:
            analytics_lines.extend([f"- #{rid}: {txt} ({'kabul' if acc else 'beklemede'})" for rid, txt, acc in routines])
        else:
            analytics_lines.append("- Oneri yok")

        plugin_lines = [f"- {name}" for name in plugins] if plugins else ["Yuklu plugin yok"]

        self._set_box(self.analytics_box, analytics_lines)
        self._set_box(self.plugins_box, plugin_lines)

    def _set_box(self, box: ctk.CTkTextbox, lines: list[str]) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", "\n".join(lines))
        box.configure(state="disabled")

    def _handle_refresh(self) -> None:
        self.on_refresh()

    def _handle_reload_plugins(self) -> None:
        self.on_reload_plugins()

    def _handle_routine_update(self) -> None:
        raw = self.routine_id_var.get().strip()
        if not raw:
            return
        try:
            rid = int(raw)
        except Exception:
            return
        accepted = self.routine_accept_var.get().strip() == "kabul"
        self.on_set_routine(rid, accepted)

    def set_theme(self, palette: dict[str, str]) -> None:
        for card in self._cards:
            try:
                card.configure(fg_color=palette["surface"], border_color=palette["surface_alt"])
            except Exception:
                pass
        for entry in self._entries:
            try:
                entry.configure(fg_color=palette["input"], text_color=palette["text"], border_color=palette["surface_alt"])
            except Exception:
                pass
        for menu in self._menus:
            try:
                menu.configure(
                    fg_color=palette["surface_alt"],
                    button_color=palette["accent"],
                    button_hover_color=palette["accent_hover"],
                    text_color=palette["text"],
                )
            except Exception:
                pass
        for btn in self._buttons:
            try:
                btn.configure(fg_color=palette["accent"], hover_color=palette["accent_hover"], text_color=palette["text"])
            except Exception:
                pass
        for box in (self.analytics_box, self.plugins_box):
            try:
                box.configure(fg_color=palette["input"], text_color=palette["text"], border_color=palette["surface_alt"])
            except Exception:
                pass
