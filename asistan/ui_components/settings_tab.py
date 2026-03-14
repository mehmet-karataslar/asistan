from __future__ import annotations

import customtkinter as ctk


class SettingsTab:
    def __init__(
        self,
        parent,
        *,
        theme_var: ctk.StringVar,
        user_name_var: ctk.StringVar,
        response_style_var: ctk.StringVar,
        security_level_var: ctk.StringVar,
        learning_mode_var: ctk.StringVar,
        profile_var: ctk.StringVar,
        db_path_text: str,
        theme_values: list[str],
        on_save_click,
    ) -> None:
        self.on_save_click = on_save_click
        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True)

        title = ctk.CTkLabel(self.root, text="Ayarlar", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w", padx=12, pady=(10, 8))

        desc = ctk.CTkLabel(
            self.root,
            text="Tema, kullanici bilgisi ve kalici kayit ayarlari bu sekmeden yonetilir.",
            justify="left",
        )
        desc.pack(anchor="w", padx=12, pady=(0, 10))

        form = ctk.CTkFrame(self.root)
        form.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(form, text="Kullanici Adi").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        self.user_name_entry = ctk.CTkEntry(form, textvariable=user_name_var, placeholder_text="ornek: Mehmet")
        self.user_name_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=(10, 4))

        ctk.CTkLabel(form, text="Tema").grid(row=1, column=0, sticky="w", padx=10, pady=4)
        self.theme_menu = ctk.CTkOptionMenu(form, values=theme_values, variable=theme_var)
        self.theme_menu.grid(row=1, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Veritabani Dosyasi").grid(row=2, column=0, sticky="w", padx=10, pady=4)
        self.db_path_entry = ctk.CTkEntry(form)
        self.db_path_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=(4, 10))
        self.db_path_entry.insert(0, db_path_text)
        self.db_path_entry.configure(state="disabled")

        ctk.CTkLabel(form, text="Cevap Stili").grid(row=3, column=0, sticky="w", padx=10, pady=4)
        self.response_style_menu = ctk.CTkOptionMenu(
            form,
            values=["samimi", "resmi", "kisa", "detayli"],
            variable=response_style_var,
        )
        self.response_style_menu.grid(row=3, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Guven Seviyesi").grid(row=4, column=0, sticky="w", padx=10, pady=4)
        self.security_level_menu = ctk.CTkOptionMenu(
            form,
            values=["dusuk", "orta", "yuksek"],
            variable=security_level_var,
        )
        self.security_level_menu.grid(row=4, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Ogrenme Modu").grid(row=5, column=0, sticky="w", padx=10, pady=4)
        self.learning_mode_menu = ctk.CTkOptionMenu(
            form,
            values=["acik", "kapali"],
            variable=learning_mode_var,
        )
        self.learning_mode_menu.grid(row=5, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Aktif Profil").grid(row=6, column=0, sticky="w", padx=10, pady=4)
        self.profile_menu = ctk.CTkOptionMenu(
            form,
            values=["varsayilan", "ev", "ofis", "oyun", "toplanti"],
            variable=profile_var,
        )
        self.profile_menu.grid(row=6, column=1, sticky="ew", padx=10, pady=(4, 10))

        form.grid_columnconfigure(1, weight=1)

        self.info_var = ctk.StringVar(value="Hazir")
        btn_row = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 8))

        self.save_btn = ctk.CTkButton(btn_row, text="Ayarlari Kaydet", command=self._handle_save)
        self.save_btn.pack(side="left")

        ctk.CTkLabel(btn_row, textvariable=self.info_var).pack(side="left", padx=10)

    def _handle_save(self) -> None:
        self.on_save_click()

    def set_info(self, text: str) -> None:
        self.info_var.set(text)

    def set_theme(self, palette: dict[str, str]) -> None:
        self.save_btn.configure(fg_color=palette["accent"], hover_color=palette["accent_hover"], text_color=palette["text"])
        self.theme_menu.configure(
            fg_color=palette["surface_alt"],
            button_color=palette["accent"],
            button_hover_color=palette["accent_hover"],
            text_color=palette["text"],
        )
        for menu in (self.response_style_menu, self.security_level_menu, self.learning_mode_menu, self.profile_menu):
            menu.configure(
                fg_color=palette["surface_alt"],
                button_color=palette["accent"],
                button_hover_color=palette["accent_hover"],
                text_color=palette["text"],
            )
        self.user_name_entry.configure(fg_color=palette["input"], text_color=palette["text"], border_color=palette["surface_alt"])
        self.db_path_entry.configure(fg_color=palette["input"], text_color=palette["muted"], border_color=palette["surface_alt"])
