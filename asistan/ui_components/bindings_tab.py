from __future__ import annotations

import unicodedata

import customtkinter as ctk


class CommandBindingsTab:
    def __init__(
        self,
        parent,
        *,
        on_refresh_apps,
        on_add_binding,
        on_remove_binding,
        on_refresh_bindings,
    ) -> None:
        self.on_refresh_apps = on_refresh_apps
        self.on_add_binding = on_add_binding
        self.on_remove_binding = on_remove_binding
        self.on_refresh_bindings = on_refresh_bindings

        self.app_var = ctk.StringVar(value="")
        self.phrase_var = ctk.StringVar(value="")
        self.remove_phrase_var = ctk.StringVar(value="")
        self.operation_var = ctk.StringVar(value="Uygulamayi Ac")
        self._app_rows: list[tuple[str, str]] = []
        self._binding_rows: list[tuple[str, str, str]] = []
        self._editing_phrase: str = ""
        self.search_var = ctk.StringVar(value="")

        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True)

        title = ctk.CTkLabel(self.root, text="Uygulama Komut Eşleme", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w", padx=12, pady=(10, 8))

        desc = ctk.CTkLabel(
            self.root,
            text="Numarali listeden uygulama secin. Komut geldiginde uygulamayi acabilir veya kapatabilirsiniz.",
            justify="left",
        )
        desc.pack(anchor="w", padx=12, pady=(0, 10))

        form = ctk.CTkFrame(self.root)
        form.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(form, text="Secilen Uygulama").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        self.selected_app_entry = ctk.CTkEntry(form, textvariable=self.app_var)
        self.selected_app_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=(10, 4))
        self.selected_app_entry.configure(state="disabled")

        ctk.CTkLabel(form, text="Islem").grid(row=1, column=0, sticky="w", padx=10, pady=4)
        self.operation_menu = ctk.CTkOptionMenu(form, values=["Uygulamayi Ac", "Uygulamayi Kapat"], variable=self.operation_var)
        self.operation_menu.grid(row=1, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Komut Cumlesi").grid(row=2, column=0, sticky="w", padx=10, pady=4)
        self.phrase_entry = ctk.CTkEntry(form, textvariable=self.phrase_var, placeholder_text="ornek: chrome ac")
        self.phrase_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Silinecek Cumle").grid(row=3, column=0, sticky="w", padx=10, pady=4)
        self.remove_entry = ctk.CTkEntry(form, textvariable=self.remove_phrase_var, placeholder_text="ornek: chrome ac")
        self.remove_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=4)

        form.grid_columnconfigure(1, weight=1)

        buttons = ctk.CTkFrame(self.root, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 8))

        self.refresh_apps_btn = ctk.CTkButton(buttons, text="Uygulamaları Yenile", command=self._handle_refresh_apps)
        self.refresh_apps_btn.pack(side="left", padx=(0, 8))

        self.add_btn = ctk.CTkButton(buttons, text="Komut Eşlemesini Kaydet", command=self._handle_add)
        self.add_btn.pack(side="left", padx=(0, 8))

        self.remove_btn = ctk.CTkButton(buttons, text="Komut Eşlemesini Sil", command=self._handle_remove)
        self.remove_btn.pack(side="left")

        self.info_var = ctk.StringVar(value="Hazır")
        self.info_label = ctk.CTkLabel(self.root, textvariable=self.info_var)
        self.info_label.pack(anchor="w", padx=12, pady=(0, 8))

        search_row = ctk.CTkFrame(self.root, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(search_row, text="Uygulama Ara", width=120, anchor="w").pack(side="left")
        self.search_entry = ctk.CTkEntry(search_row, textvariable=self.search_var, placeholder_text="ornek: chrome")
        self.search_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(self.root, text="Uygulama Listesi (numarali)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(2, 6))
        self.apps_scroll = ctk.CTkScrollableFrame(self.root, height=230)
        self.apps_scroll.pack(fill="x", padx=12, pady=(0, 10))
        self.apps_scroll.bind("<MouseWheel>", self._on_mouse_wheel)

        self.search_var.trace_add("write", lambda *_: self._apply_filter())

        ctk.CTkLabel(self.root, text="Kayitli Komutlar", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(2, 6))
        self.bindings_scroll = ctk.CTkScrollableFrame(self.root, height=300)
        self.bindings_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.bindings_scroll.bind("<MouseWheel>", self._on_bindings_mouse_wheel)
        self._set_add_button_edit_mode(False)

    def set_apps(self, app_rows: list[tuple[str, str]]) -> None:
        self._app_rows = app_rows
        self._apply_filter()

    def _apply_filter(self) -> None:
        needle = self._normalize(self.search_var.get())
        if not needle:
            self._render_apps(self._app_rows)
            return

        # Önce tam alt dizi ara
        exact = [(d, t) for d, t in self._app_rows if needle in self._normalize(d)]
        if exact:
            self._render_apps(exact)
            return

        # Yaklaşık eşleşme: iğne karakterleri sırayla geçiyor mu?
        fuzzy = [(d, t) for d, t in self._app_rows if self._fuzzy_match(needle, self._normalize(d))]
        if fuzzy:
            self._render_apps(fuzzy)
            return

        # Hiç eşleşme yoksa tüm listeyi koru
        self.set_info("Eslesme bulunamadi, tum liste gosteriliyor")
        self._render_apps(self._app_rows)

    def _render_apps(self, app_rows: list[tuple[str, str]]) -> None:
        for child in self.apps_scroll.winfo_children():
            child.destroy()

        if not app_rows:
            ctk.CTkLabel(self.apps_scroll, text="(eslesen uygulama bulunamadi)").pack(anchor="w", padx=4, pady=4)
            return

        for idx, (display, target) in enumerate(app_rows, start=1):
            row = ctk.CTkFrame(self.apps_scroll, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=2)

            badge = ctk.CTkLabel(row, text=f"{idx:03}", width=44, anchor="center")
            badge.pack(side="left", padx=(0, 6))

            # Uygulama icon'u yerine hizli gorunur rozet (ilk harf).
            icon_text = display[:1].upper() if display else "?"
            icon = ctk.CTkLabel(row, text=icon_text, width=24)
            icon.pack(side="left", padx=(0, 8))

            btn = ctk.CTkButton(
                row,
                text=display,
                anchor="w",
                command=lambda d=display: self._select_app(d),
            )
            btn.pack(side="left", fill="x", expand=True)

            row.bind("<MouseWheel>", self._on_mouse_wheel)
            badge.bind("<MouseWheel>", self._on_mouse_wheel)
            icon.bind("<MouseWheel>", self._on_mouse_wheel)
            btn.bind("<MouseWheel>", self._on_mouse_wheel)

        self._select_app(app_rows[0][0])

    def set_bindings(self, rows: list[tuple[str, str, str]]) -> None:
        self._binding_rows = rows
        if self._editing_phrase:
            normalized = self._normalize(self._editing_phrase)
            still_exists = any(self._normalize(phrase) == normalized for phrase, _app, _op in rows)
            if not still_exists:
                self.clear_editing_selection()
        self._render_bindings()

    def set_bindings_text(self, content: str) -> None:
        """Geriye donuk uyumluluk icin metin tabanli yontem."""
        if not content or content.strip() == "Kayitli esleme yok":
            self.set_bindings([])

    def _render_bindings(self) -> None:
        for child in self.bindings_scroll.winfo_children():
            child.destroy()

        if not self._binding_rows:
            ctk.CTkLabel(self.bindings_scroll, text="(kayitli komut eslemesi yok)").pack(anchor="w", padx=4, pady=4)
            return

        for idx, (phrase, app_display, operation) in enumerate(self._binding_rows, start=1):
            row = ctk.CTkFrame(self.bindings_scroll, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=2)

            badge = ctk.CTkLabel(row, text=f"{idx:03}", width=44, anchor="center")
            badge.pack(side="left", padx=(0, 6))

            op_label = "ac" if operation == "ac" else "kapat"
            text = f"{phrase} -> {app_display} ({op_label})"
            btn = ctk.CTkButton(
                row,
                text=text,
                anchor="w",
                command=lambda p=phrase, a=app_display, op=operation: self._select_binding(p, a, op),
            )
            btn.pack(side="left", fill="x", expand=True)

            row.bind("<MouseWheel>", self._on_bindings_mouse_wheel)
            badge.bind("<MouseWheel>", self._on_bindings_mouse_wheel)
            btn.bind("<MouseWheel>", self._on_bindings_mouse_wheel)

    def set_info(self, text: str) -> None:
        self.info_var.set(text)

    def selected_app(self) -> str:
        return self.app_var.get().strip()

    def selected_operation(self) -> str:
        return "kapat" if self.operation_var.get().strip() == "Uygulamayi Kapat" else "ac"

    def editing_phrase(self) -> str:
        return self._editing_phrase

    def phrase(self) -> str:
        return self.phrase_var.get().strip()

    def remove_phrase(self) -> str:
        return self.remove_phrase_var.get().strip()

    def clear_phrase(self) -> None:
        self.phrase_var.set("")

    def clear_remove_phrase(self) -> None:
        self.remove_phrase_var.set("")

    def clear_editing_selection(self) -> None:
        self._editing_phrase = ""
        self._set_add_button_edit_mode(False)

    def _handle_refresh_apps(self) -> None:
        self.on_refresh_apps()

    def _handle_add(self) -> None:
        self.on_add_binding()

    def _handle_remove(self) -> None:
        self.on_remove_binding()

    def refresh_bindings_view(self) -> None:
        self.on_refresh_bindings()

    def _select_app(self, display_name: str) -> None:
        self.app_var.set(display_name)

    def _select_binding(self, phrase: str, app_display: str, operation: str) -> None:
        self._editing_phrase = phrase
        self.app_var.set(app_display)
        self.phrase_var.set(phrase)
        self.remove_phrase_var.set(phrase)
        self.operation_var.set("Uygulamayi Kapat" if operation == "kapat" else "Uygulamayi Ac")
        self._set_add_button_edit_mode(True)
        self.set_info(f"Duzenleme modu: '{phrase}'")

    def _set_add_button_edit_mode(self, is_editing: bool) -> None:
        text = "Komut Eşlemesini Güncelle" if is_editing else "Komut Eşlemesini Kaydet"
        self.add_btn.configure(text=text)

    def set_theme(self, palette: dict[str, str]) -> None:
        self.refresh_apps_btn.configure(fg_color=palette["accent"], hover_color=palette["accent_hover"], text_color=palette["text"])
        self.add_btn.configure(fg_color=palette["success"], hover_color=palette["success_hover"], text_color=palette["text"])
        self.remove_btn.configure(fg_color=palette["danger"], hover_color=palette["danger_hover"], text_color=palette["text"])

        self.operation_menu.configure(
            fg_color=palette["surface_alt"],
            button_color=palette["accent"],
            button_hover_color=palette["accent_hover"],
            text_color=palette["text"],
        )

        for entry in (self.selected_app_entry, self.phrase_entry, self.remove_entry, self.search_entry):
            entry.configure(fg_color=palette["input"], text_color=palette["text"], border_color=palette["surface_alt"])

        self.bindings_scroll.configure(fg_color=palette["input"], border_color=palette["surface_alt"])

    def _normalize(self, value: str) -> str:
        lowered = value.casefold().strip()
        normalized = unicodedata.normalize("NFKD", lowered)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    def _fuzzy_match(self, needle: str, haystack: str) -> bool:
        """Tüm needle karakterleri haystack'te sırayla geçiyorsa True."""
        it = iter(haystack)
        return all(ch in it for ch in needle)

    def _on_mouse_wheel(self, event) -> str:
        try:
            direction = -1 if event.delta > 0 else 1
            steps = max(1, abs(int(event.delta)) // 120) * 4
            self.apps_scroll._parent_canvas.yview_scroll(direction * steps, "units")
        except Exception:
            pass
        return "break"

    def _on_bindings_mouse_wheel(self, event) -> str:
        try:
            direction = -1 if event.delta > 0 else 1
            steps = max(1, abs(int(event.delta)) // 120) * 4
            self.bindings_scroll._parent_canvas.yview_scroll(direction * steps, "units")
        except Exception:
            pass
        return "break"
