from __future__ import annotations

import time
from tkinter import PhotoImage, messagebox

import customtkinter as ctk

from .. import APP_NAME
from ..actions import SystemActions
from ..app_catalog import discover_installed_apps
from ..app_launcher import close_application, launch_application
from ..audio import ClapDetector
from ..command_bindings import CommandBindingStore, normalize_text
from ..command_parser import ParsedCommand, TurkishCommandParser
from ..paths import db_file_path, ensure_user_plugins_seeded, icon_ico_path, icon_png_path, get_autostart, set_autostart
from ..mic_monitor import MicrophoneMonitor
from ..plugins import PluginManager
from ..scheduler import TaskScheduler
from ..config.sqlite_store import SQLiteStore
from ..settings import ActionSettings, AppState, DetectionSettings, UiSettings, VoiceSettings
from ..speech import VoiceKeywordDetector
from .bindings_tab import CommandBindingsTab
from .akilli_ozellikler_tab import AkilliOzelliklerTab
from .design import THEME_PALETTES
from .pencere_tab import PencereTab
from .senaryolar_tab import SenaryolarTab
from .settings_tab import SettingsTab
from .sistem_kontrol_tab import SistemKontrolTab

ALGILAMA_TURLERI = {"Sesli Komut": "sesli_komut", "El Cirpma": "el_cirpma"}
KOMUT_MODLARI = {"Dogal Komut": "dogal", "Anahtar Kelime": "anahtar"}
SES_MOTORLERI = {
    "Cevrimici (Whisper TR)": "cevrimici_whisper",
    "Cevrimici (Google)": "cevrimici",
    "Cevrimdisi (Vosk)": "cevrimdisi",
}
EYLEM_TURLERI = {
    "Uyku Moduna Gec": "uyku",
    "Bilgisayari Kapat": "kapat",
    "Ozel Komut Calistir": "ozel_komut",
}


class AsistanApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1180x790")
        self.root.minsize(1020, 700)

        self.db_path = db_file_path()
        self.store = SQLiteStore(self.db_path)
        self.store.initialize()
        self.state, saved_bindings = self.store.load()

        if self.state.ui.theme not in THEME_PALETTES:
            self.state.ui.theme = "Neon Gece"

        self.palette = THEME_PALETTES[self.state.ui.theme]
        self.cards: list[ctk.CTkFrame] = []
        self._loading_state = True
        self._persist_ready = False

        self.actions = SystemActions(self.log, self.set_status)
        self.scheduler = TaskScheduler(self.log)
        self.clap_detector = ClapDetector(self.on_clap_event, self.on_audio_error)
        self.voice_detector = VoiceKeywordDetector(self.on_phrase_event, self.on_audio_error)
        self.mic_monitor = MicrophoneMonitor()
        self.binding_store = CommandBindingStore()
        self.binding_store.load_items(saved_bindings)

        self.available_apps: list[tuple[str, str]] = []
        self.app_targets_by_display: dict[str, str] = {}
        self.mic_test_after_id = None

        self.status_var = ctk.StringVar(value="Hazir")
        self.mode_var = ctk.StringVar(value="Sesli Komut")
        self.threshold_var = ctk.DoubleVar(value=self.state.detection.threshold)
        self.required_claps_var = ctk.StringVar(value=str(self.state.detection.required_claps))
        self.window_seconds_var = ctk.StringVar(value=str(self.state.detection.window_seconds))
        self.min_clap_gap_var = ctk.StringVar(value=str(self.state.detection.min_clap_gap))
        self.cooldown_var = ctk.StringVar(value=str(self.state.detection.cooldown))
        self.samplerate_var = ctk.StringVar(value=str(self.state.detection.samplerate))
        self.voice_keyword_var = ctk.StringVar(value=self.state.voice.keyword)
        self.command_mode_var = ctk.StringVar(value="Dogal Komut")
        self.recognition_engine_var = ctk.StringVar(value="Cevrimici (Whisper TR)")
        self.vosk_model_path_var = ctk.StringVar(value=self.state.voice.vosk_model_path)
        self.voice_phrase_limit_var = ctk.DoubleVar(value=self.state.voice.phrase_time_limit)
        self.voice_level_var = ctk.StringVar(value=str(self.state.voice.min_voice_level))
        self.system_audio_filter_var = ctk.StringVar(value="Acik" if self.state.voice.filter_system_audio else "Kapali")
        self.action_var = ctk.StringVar(value="Uyku Moduna Gec")
        self.custom_command_var = ctk.StringVar(value=self.state.action.custom_command)
        self.theme_var = ctk.StringVar(value=self.state.ui.theme)
        self.user_name_var = ctk.StringVar(value=self.state.ui.user_name)
        self.response_style_var = ctk.StringVar(value=self.state.ui.response_style)
        self.security_level_var = ctk.StringVar(value=self.state.ui.security_level)
        self.profile_var = ctk.StringVar(value=self.state.ui.active_profile)
        self.autostart_var = ctk.BooleanVar(value=get_autostart())
        self._last_app_context = ""
        self.plugin_manager = PluginManager(ensure_user_plugins_seeded())

        self.mic_test_status_var = ctk.StringVar(value="Hazir")
        self.mic_test_db_var = ctk.StringVar(value="dBFS: -120.0")
        self.mic_test_peak_var = ctk.StringVar(value="Peak: 0.00")
        self.mic_test_rate_var = ctk.StringVar(value="Ornekleme: -")
        self._mic_test_db_samples: list[float] = []
        self._mic_test_peak_samples: list[float] = []
        self._mic_test_started_at: float = 0.0

        self._build_ui()
        self._apply_selected_theme(force=True)
        self._bind_events()
        self._hydrate_ui_from_state()
        self.sync_state()
        self._set_initial_messages()
        self._loading_state = False
        self._persist_ready = True

    def _build_ui(self) -> None:
        ctk.set_appearance_mode("dark")
        self.root.configure(fg_color=self.palette["bg"])

        self.main = ctk.CTkFrame(self.root, fg_color=self.palette["bg"], corner_radius=0)
        self.main.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        self.title_label = ctk.CTkLabel(header, text="Asistan", font=ctk.CTkFont(size=32, weight="bold"), text_color=self.palette["text"])
        self.title_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(
            header,
            text="Sesli komut, el cirpma ve uygulama komut esleme ile sistem kontrolu.",
            text_color=self.palette["muted"],
        )
        self.subtitle_label.pack(anchor="w")

        self.tabview = ctk.CTkTabview(self.main)
        self.tabview.pack(fill="both", expand=True)
        self.tabview.add("Asistan")
        self.tabview.add("Komut Esleme")
        self.tabview.add("Sistem Kontrolu")
        self.tabview.add("Senaryolar")
        self.tabview.add("Pencere Yonetimi")
        self.tabview.add("Akilli Ozellikler")
        self.tabview.add("Ayarlar")

        self.main_tab = self.tabview.tab("Asistan")
        self.bindings_tab_frame = self.tabview.tab("Komut Esleme")
        self.settings_tab_frame = self.tabview.tab("Ayarlar")

        self._build_dashboard_tab(self.main_tab)
        self._build_settings_content()

        self.bindings_tab = CommandBindingsTab(
            self.bindings_tab_frame,
            on_refresh_apps=self.refresh_app_list,
            on_add_binding=self.add_phrase_binding,
            on_remove_binding=self.remove_phrase_binding,
            on_refresh_bindings=self.refresh_bindings_preview,
        )

        self.sistem_kontrol_tab_obj = SistemKontrolTab(
            self.tabview.tab("Sistem Kontrolu"),
            on_test_action=self._test_system_action,
            on_save=self._save_system_phrases,
        )

        self.senaryolar_tab_obj = SenaryolarTab(
            self.tabview.tab("Senaryolar"),
            on_save=self._save_scenarios,
            on_test_scenario=self._test_scenario,
        )

        self.pencere_tab_obj = PencereTab(
            self.tabview.tab("Pencere Yonetimi"),
            on_test_action=self._test_window_action,
            on_save=self._save_window_phrases,
            on_named_window_action=self._test_named_window_action,
        )

        self.akilli_ozellikler_tab = AkilliOzelliklerTab(
            self.tabview.tab("Akilli Ozellikler"),
            on_refresh=self._refresh_smart_features_tab,
            on_set_routine=self._set_routine_status,
            on_reload_plugins=self._reload_plugins,
        )

    def _build_dashboard_tab(self, parent) -> None:
        hero = self._card(parent)
        hero.pack(fill="x", pady=(8, 10), padx=6)

        ctk.CTkLabel(
            hero,
            text="Komut Merkezi",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(
            hero,
            text="Asistanin tum yeteneklerini buradan gorebilirsiniz. Ayarlamalar Ayarlar sekmesinde.",
            text_color=self.palette["muted"],
        ).pack(anchor="w", padx=14, pady=(0, 10))

        quick = ctk.CTkFrame(hero, fg_color="transparent")
        quick.pack(fill="x", padx=12, pady=(0, 10))

        self.start_btn = ctk.CTkButton(quick, text="Devreye Al", command=self.start_monitoring, width=170)
        self.start_btn.pack(side="left", padx=(2, 8), pady=2)
        self.stop_btn = ctk.CTkButton(quick, text="Dinlemeyi Durdur", command=self.stop_monitoring, width=170, state="disabled")
        self.stop_btn.pack(side="left", padx=8, pady=2)
        self.test_btn = ctk.CTkButton(quick, text="Secili Eylemi Test Et", command=self.test_selected_action, width=200)
        self.test_btn.pack(side="left", padx=8, pady=2)
        self.status_chip = ctk.CTkLabel(quick, textvariable=self.status_var, width=220, anchor="center")
        self.status_chip.pack(side="right", padx=(8, 2), pady=2)

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

        commands = self._card(grid)
        commands.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self._section_title(commands, "Populer Komutlar")
        self.command_showcase = ctk.CTkTextbox(commands, height=200)
        self.command_showcase.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.command_showcase.configure(state="disabled")

        scenarios = self._card(grid)
        scenarios.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        self._section_title(scenarios, "Hazir Senaryolar")
        self.scenario_showcase = ctk.CTkTextbox(scenarios, height=200)
        self.scenario_showcase.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.scenario_showcase.configure(state="disabled")

        tips = self._card(grid)
        tips.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(6, 0))
        self._section_title(tips, "Neler Yapabilir?")
        self.tips_showcase = ctk.CTkTextbox(tips, height=200)
        self.tips_showcase.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tips_showcase.configure(state="disabled")

        log_card = self._card(grid)
        log_card.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(6, 0))
        self._build_log_card(log_card)

    def _build_settings_content(self) -> None:
        settings_scroll = ctk.CTkScrollableFrame(self.settings_tab_frame)
        settings_scroll.pack(fill="both", expand=True)

        core_settings = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        core_settings.pack(fill="x", padx=6, pady=(6, 8))

        self.settings_tab = SettingsTab(
            core_settings,
            theme_var=self.theme_var,
            user_name_var=self.user_name_var,
            response_style_var=self.response_style_var,
            security_level_var=self.security_level_var,
            profile_var=self.profile_var,
            autostart_var=self.autostart_var,
            db_path_text=str(self.db_path),
            theme_values=list(THEME_PALETTES.keys()),
            on_save_click=self.save_all_to_db,
        )

        settings_grid = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        settings_grid.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        settings_grid.grid_columnconfigure(0, weight=3)
        settings_grid.grid_columnconfigure(1, weight=2)
        settings_grid.grid_rowconfigure(0, weight=1)
        settings_grid.grid_rowconfigure(1, weight=1)

        left_top = self._card(settings_grid)
        left_top.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self._build_trigger_card(left_top)

        right_top = self._card(settings_grid)
        right_top.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        self._build_action_card(right_top)

        left_bottom = self._card(settings_grid)
        left_bottom.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(6, 0))
        self._build_clap_card(left_bottom)

    def _card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=self.palette["surface"], corner_radius=16, border_width=1, border_color=self.palette["surface_alt"])
        self.cards.append(card)
        return card

    def _row(self, parent, label_text: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text=label_text, width=170, anchor="w").pack(side="left")
        return row

    def _section_title(self, parent, text: str) -> None:
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

    def _build_trigger_card(self, parent) -> None:
        self._section_title(parent, "Tetikleme Ayarlari")

        row = self._row(parent, "Algilama")
        self.mode_menu = ctk.CTkOptionMenu(row, values=list(ALGILAMA_TURLERI.keys()), variable=self.mode_var)
        self.mode_menu.pack(side="left", fill="x", expand=True)

        row = self._row(parent, "Anahtar Kelime")
        self.voice_keyword_entry = ctk.CTkEntry(row, textvariable=self.voice_keyword_var)
        self.voice_keyword_entry.pack(side="left", fill="x", expand=True)

        row = self._row(parent, "Komut Modu")
        self.command_mode_menu = ctk.CTkOptionMenu(row, values=list(KOMUT_MODLARI.keys()), variable=self.command_mode_var)
        self.command_mode_menu.pack(side="left", fill="x", expand=True)

        row = self._row(parent, "Ses Motoru")
        self.recognition_engine_menu = ctk.CTkOptionMenu(row, values=list(SES_MOTORLERI.keys()), variable=self.recognition_engine_var)
        self.recognition_engine_menu.pack(side="left", fill="x", expand=True)

        row = self._row(parent, "Vosk Model")
        self.vosk_model_entry = ctk.CTkEntry(row, textvariable=self.vosk_model_path_var)
        self.vosk_model_entry.pack(side="left", fill="x", expand=True)

        row = self._row(parent, "Dinleme Suresi")
        self.voice_limit_slider = ctk.CTkSlider(row, from_=1.0, to=5.0, variable=self.voice_phrase_limit_var)
        self.voice_limit_slider.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.voice_limit_label = ctk.CTkLabel(row, text="2.4 sn", width=64)
        self.voice_limit_label.pack(side="left")

        row = self._row(parent, "Ses Esigi")
        self.voice_level_entry = ctk.CTkEntry(row, textvariable=self.voice_level_var, width=120)
        self.voice_level_entry.pack(side="left")

        row = self._row(parent, "Sistem Sesi Filtresi")
        self.system_audio_filter_menu = ctk.CTkOptionMenu(row, values=["Acik", "Kapali"], variable=self.system_audio_filter_var)
        self.system_audio_filter_menu.pack(side="left", fill="x", expand=True)

        test_box = ctk.CTkFrame(parent)
        test_box.pack(fill="x", padx=12, pady=(8, 6))
        ctk.CTkLabel(test_box, text="Mikrofon Testi", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=8, pady=(8, 4))
        self.mic_test_button = ctk.CTkButton(test_box, text="Mikrofon Testini Baslat", command=self.toggle_mic_test)
        self.mic_test_button.pack(anchor="w", padx=8, pady=(0, 6))
        self.mic_test_bar = ctk.CTkProgressBar(test_box)
        self.mic_test_bar.pack(fill="x", padx=8, pady=(0, 6))
        self.mic_test_bar.set(0.0)
        ctk.CTkLabel(test_box, textvariable=self.mic_test_status_var).pack(anchor="w", padx=8)
        ctk.CTkLabel(test_box, textvariable=self.mic_test_db_var).pack(anchor="w", padx=8)
        ctk.CTkLabel(test_box, textvariable=self.mic_test_peak_var).pack(anchor="w", padx=8)
        ctk.CTkLabel(test_box, textvariable=self.mic_test_rate_var).pack(anchor="w", padx=8, pady=(0, 8))

        self.trigger_help_label = ctk.CTkLabel(parent, text="")
        self.trigger_help_label.pack(anchor="w", padx=12, pady=(4, 8))

    def _build_action_card(self, parent) -> None:
        self._section_title(parent, "Eylem Ayarlari")
        row = self._row(parent, "Eylem")
        self.action_menu = ctk.CTkOptionMenu(row, values=list(EYLEM_TURLERI.keys()), variable=self.action_var)
        self.action_menu.pack(side="left", fill="x", expand=True)

        row = self._row(parent, "Ozel Komut")
        self.custom_command_entry = ctk.CTkEntry(row, textvariable=self.custom_command_var)
        self.custom_command_entry.pack(side="left", fill="x", expand=True)

        self.action_help_label = ctk.CTkLabel(parent, text="", justify="left", wraplength=320)
        self.action_help_label.pack(anchor="w", padx=12, pady=(6, 8))

    def _build_clap_card(self, parent) -> None:
        self._section_title(parent, "El Cirpma Ayarlari")
        row = self._row(parent, "Hassasiyet")
        self.threshold_slider = ctk.CTkSlider(row, from_=0.2, to=1.0, variable=self.threshold_var)
        self.threshold_slider.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.threshold_label = ctk.CTkLabel(row, text="0.82", width=60)
        self.threshold_label.pack(side="left")

        row = self._row(parent, "Clap Sayisi")
        self.required_entry = ctk.CTkEntry(row, textvariable=self.required_claps_var, width=120)
        self.required_entry.pack(side="left")

        row = self._row(parent, "Pencere (sn)")
        self.window_entry = ctk.CTkEntry(row, textvariable=self.window_seconds_var, width=120)
        self.window_entry.pack(side="left")

        row = self._row(parent, "Min Aralik (sn)")
        self.min_gap_entry = ctk.CTkEntry(row, textvariable=self.min_clap_gap_var, width=120)
        self.min_gap_entry.pack(side="left")

        row = self._row(parent, "Cooldown (sn)")
        self.cooldown_entry = ctk.CTkEntry(row, textvariable=self.cooldown_var, width=120)
        self.cooldown_entry.pack(side="left")

        row = self._row(parent, "Ornekleme")
        self.samplerate_menu = ctk.CTkOptionMenu(row, values=["16000", "22050", "44100", "48000"], variable=self.samplerate_var)
        self.samplerate_menu.pack(side="left", fill="x", expand=True)

    def _build_log_card(self, parent) -> None:
        self._section_title(parent, "Durum ve Kayit")
        self.status_label = ctk.CTkLabel(parent, textvariable=self.status_var, font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(anchor="w", padx=12, pady=(2, 4))

        self.log_text = ctk.CTkTextbox(parent)
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_text.configure(state="disabled")

    def _bind_events(self) -> None:
        vars_to_bind = [
            self.mode_var,
            self.threshold_var,
            self.required_claps_var,
            self.window_seconds_var,
            self.min_clap_gap_var,
            self.cooldown_var,
            self.samplerate_var,
            self.voice_keyword_var,
            self.command_mode_var,
            self.recognition_engine_var,
            self.vosk_model_path_var,
            self.voice_phrase_limit_var,
            self.voice_level_var,
            self.system_audio_filter_var,
            self.action_var,
            self.custom_command_var,
            self.theme_var,
            self.user_name_var,
            self.response_style_var,
            self.security_level_var,
            self.profile_var,
        ]
        for item in vars_to_bind:
            item.trace_add("write", lambda *_: self.sync_state())

    def _set_initial_messages(self) -> None:
        self._load_active_profile_snapshot()
        self.log("Asistan baslatildi.")
        self.log("Komut Esleme sekmesinden uygulama + cumle baglayabilirsiniz.")
        self.log(f"SQLite dosyasi: {self.db_path}")
        if self.state.ui.user_name:
            self.log(f"Hos geldin {self.state.ui.user_name}")
        self._populate_dashboard_content()
        self._init_custom_phrases()
        self._init_plugins()
        self._refresh_smart_features_tab()
        self.refresh_app_list()
        self.refresh_bindings_preview()

    def _load_active_profile_snapshot(self) -> None:
        pid = self.state.ui.active_profile.strip()
        if not pid:
            return
        for profile_id, _name, payload in self.store.load_profiles():
            if profile_id != pid:
                continue
            try:
                detection = payload.get("detection") or {}
                voice = payload.get("voice") or {}
                self.state.detection.mode = str(detection.get("mode", self.state.detection.mode))
                self.state.voice.keyword = str(voice.get("keyword", self.state.voice.keyword))
                self.state.voice.command_mode = str(voice.get("command_mode", self.state.voice.command_mode))
            except Exception:
                pass
            self._hydrate_ui_from_state()
            self.sync_state()
            return

    def _save_current_profile_snapshot(self) -> None:
        pid = self.state.ui.active_profile.strip() or "varsayilan"
        payload = {
            "detection": {
                "mode": self.state.detection.mode,
            },
            "voice": {
                "keyword": self.state.voice.keyword,
                "command_mode": self.state.voice.command_mode,
            },
        }
        self.store.save_profile(pid, pid.title(), payload)

    def _init_plugins(self) -> None:
        loaded = self.plugin_manager.load_all()
        if loaded:
            self.log(self._style_message(f"Pluginler yuklendi: {', '.join(loaded)}"))

    def _refresh_smart_features_tab(self) -> None:
        analytics = self.store.load_history_summary(limit=20)
        routines = self.store.load_routine_suggestions(limit=20)
        plugins = [getattr(p, "__name__", "plugin") for p in self.plugin_manager.plugins]
        self.akilli_ozellikler_tab.set_data(
            analytics=analytics,
            routines=routines,
            plugins=plugins,
        )
        self.akilli_ozellikler_tab.set_info("Veriler guncellendi")

    def _set_routine_status(self, suggestion_id: int, accepted: bool) -> None:
        changed = self.store.set_routine_suggestion_status(suggestion_id, accepted)
        self.akilli_ozellikler_tab.set_info("Rutin guncellendi" if changed else "ID bulunamadi")
        self._refresh_smart_features_tab()

    def _reload_plugins(self) -> None:
        loaded = self.plugin_manager.load_all()
        self.akilli_ozellikler_tab.set_info(
            f"Pluginler yuklendi: {', '.join(loaded)}" if loaded else "Plugin bulunamadi"
        )
        self._refresh_smart_features_tab()

    def _style_message(self, message: str) -> str:
        style = self.state.ui.response_style
        if style == "resmi":
            return f"[Bilgi] {message}"
        if style == "kisa":
            return message.split(".")[0]
        if style == "detayli":
            return f"Detay: {message}"
        return message

    def _log_history(self, transcript: str, action: str, success: bool, source: str) -> None:
        try:
            self.store.save_history(transcript, action, success, source)
        except Exception:
            pass

    def _should_confirm_risky(self, action: str) -> bool:
        return self.state.ui.security_level == "yuksek" and action in {"kapat", "yeniden_baslat", "wifi_kapat", "bluetooth_kapat"}

    def _maybe_suggest_routine(self) -> None:
        try:
            top = self.store.load_history_summary(limit=5)
            if not top:
                return
            action, total, _ok = top[0]
            if total >= 7:
                self.store.save_routine_suggestion(f"{action} eylemi sik kullaniliyor. Otomatik rutin onerisi.", accepted=False)
        except Exception:
            pass

    def _populate_dashboard_content(self) -> None:
        popular_lines = [
            "- chrome ac: Uygulamayi baslatir",
            "- discord kapat: Uygulamayi kapatir",
            "- sesi kis 5: Ses seviyesini dusurur",
            "- parlakligi arttir 20: Ekrani aydinlatir",
            "- wifi kapat: Kablosuz baglantiyi kapatir",
            "- bluetooth ac: Bluetooth'u aktif eder",
            "- ekrani kilitle: Aninda kilit ekranina gecer",
            "- ekran goruntusu al: PNG ekran goruntusu kaydeder",
            "- aktif pencereyi sola yasla: Pencereyi sol yariya alir",
        ]
        scenario_lines = [
            "Ders Modu: Sessize al + parlakligi dusur + tum pencereleri kucult",
            "Is Modu: WiFi ac + parlakligi arttir + sesi kis",
            "Oyun Modu: Parlakligi arttir + sesi ac",
            "Toplanti Modu: Sessize al + parlakligi biraz arttir",
            "Gece Modu: Parlakligi azalt + sesi kis",
            "",
            "Not: Senaryolar sekmesinden adimlari ve tetikleyici cumleyi degistirebilirsin.",
        ]
        tips_lines = [
            "1) Once Ayarlar sekmesinden tetikleme ve ses motorunu sec.",
            "2) Komut Esleme sekmesinden uygulama-ac/kapat cumleleri ekle.",
            "3) Sistem Kontrolu sekmesinde komut ifadelerini kisilestir.",
            "4) Pencere Yonetimi sekmesinde aktif ve isimli pencere kontrollerini test et.",
            "5) Senaryolar sekmesinden cok adimli otomasyonlar kur.",
            "",
            "Ornek cumle: yarim saat sonra bilgisayari kapat",
        ]

        try:
            summary = self.store.load_history_summary(limit=5)
            if summary:
                tips_lines.append("")
                tips_lines.append("Son Kullanim Analitigi:")
                for action, total, ok in summary:
                    rate = int((ok / total) * 100) if total else 0
                    tips_lines.append(f"- {action}: {total} kez, %{rate} basari")
            suggestions = self.store.load_routine_suggestions(limit=3)
            if suggestions:
                tips_lines.append("")
                tips_lines.append("Rutin Onerileri:")
                for _sid, rule, accepted in suggestions:
                    state = "kabul" if accepted else "beklemede"
                    tips_lines.append(f"- {rule} ({state})")
        except Exception:
            pass

        for widget, lines in (
            (self.command_showcase, popular_lines),
            (self.scenario_showcase, scenario_lines),
            (self.tips_showcase, tips_lines),
        ):
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("end", "\n".join(lines))
            widget.configure(state="disabled")

    def _to_float(self, raw: str, fallback: float) -> float:
        try:
            return float(str(raw).strip().replace(",", "."))
        except Exception:
            return fallback

    def _to_int(self, raw: str, fallback: int) -> int:
        try:
            return int(float(str(raw).strip().replace(",", ".")))
        except Exception:
            return fallback

    def _safe_config(self, widget, **kwargs) -> None:
        try:
            widget.configure(**kwargs)
        except Exception:
            pass

    def _map_key(self, mapping: dict[str, str], label: str, default_value: str) -> str:
        return mapping.get(label, default_value)

    def _map_label(self, mapping: dict[str, str], value: str, default_label: str) -> str:
        for label, mapped in mapping.items():
            if mapped == value:
                return label
        return default_label

    def _hydrate_ui_from_state(self) -> None:
        self.mode_var.set(self._map_label(ALGILAMA_TURLERI, self.state.detection.mode, "Sesli Komut"))
        self.threshold_var.set(float(self.state.detection.threshold))
        self.required_claps_var.set(str(self.state.detection.required_claps))
        self.window_seconds_var.set(str(self.state.detection.window_seconds))
        self.min_clap_gap_var.set(str(self.state.detection.min_clap_gap))
        self.cooldown_var.set(str(self.state.detection.cooldown))
        self.samplerate_var.set(str(self.state.detection.samplerate))

        self.voice_keyword_var.set(self.state.voice.keyword)
        self.command_mode_var.set(self._map_label(KOMUT_MODLARI, self.state.voice.command_mode, "Dogal Komut"))
        self.recognition_engine_var.set(self._map_label(SES_MOTORLERI, self.state.voice.recognition_engine, "Cevrimici (Whisper TR)"))
        self.vosk_model_path_var.set(self.state.voice.vosk_model_path)
        self.voice_phrase_limit_var.set(float(self.state.voice.phrase_time_limit))
        self.voice_level_var.set(str(self.state.voice.min_voice_level))
        self.system_audio_filter_var.set("Acik" if self.state.voice.filter_system_audio else "Kapali")

        self.action_var.set(self._map_label(EYLEM_TURLERI, self.state.action.action, "Uyku Moduna Gec"))
        self.custom_command_var.set(self.state.action.custom_command)

        if self.state.ui.theme not in THEME_PALETTES:
            self.state.ui.theme = "Neon Gece"
        self.theme_var.set(self.state.ui.theme)
        self.user_name_var.set(self.state.ui.user_name)
        self.response_style_var.set(self.state.ui.response_style)
        self.security_level_var.set(self.state.ui.security_level)
        self.profile_var.set(self.state.ui.active_profile)

    def sync_state(self) -> None:
        self.state.detection = DetectionSettings(
            mode=self._map_key(ALGILAMA_TURLERI, self.mode_var.get().strip(), "sesli_komut"),
            threshold=float(self.threshold_var.get()),
            required_claps=max(1, self._to_int(self.required_claps_var.get(), 2)),
            window_seconds=self._to_float(self.window_seconds_var.get(), 1.2),
            min_clap_gap=self._to_float(self.min_clap_gap_var.get(), 0.35),
            cooldown=self._to_float(self.cooldown_var.get(), 10.0),
            samplerate=self._to_int(self.samplerate_var.get(), 44100),
        )
        self.state.voice = VoiceSettings(
            keyword=self.voice_keyword_var.get().strip(),
            command_mode=self._map_key(KOMUT_MODLARI, self.command_mode_var.get().strip(), "dogal"),
            recognition_engine=self._map_key(SES_MOTORLERI, self.recognition_engine_var.get().strip(), "cevrimici_whisper"),
            phrase_time_limit=max(1.0, min(5.0, float(self.voice_phrase_limit_var.get()))),
            samplerate=16000,
            cooldown=self._to_float(self.cooldown_var.get(), 8.0),
            min_voice_level=max(200, self._to_int(self.voice_level_var.get(), 900)),
            vosk_model_path=self.vosk_model_path_var.get().strip(),
            filter_system_audio=self.system_audio_filter_var.get().strip().casefold() == "acik",
        )
        self.state.action = ActionSettings(
            action=self._map_key(EYLEM_TURLERI, self.action_var.get().strip(), "uyku"),
            custom_command=self.custom_command_var.get().strip(),
        )

        selected_theme = self.theme_var.get().strip()
        if selected_theme not in THEME_PALETTES:
            selected_theme = "Neon Gece"
        self.state.ui = UiSettings(
            theme=selected_theme,
            user_name=self.user_name_var.get().strip(),
            response_style=self.response_style_var.get().strip() or "samimi",
            security_level=self.security_level_var.get().strip() or "orta",
            active_profile=self.profile_var.get().strip() or "varsayilan",
        )

        self.clap_detector.update_settings(self.state.detection)
        self.voice_detector.update_settings(self.state.voice)

        self.threshold_label.configure(text=f"{self.threshold_var.get():.2f}")
        self.voice_limit_label.configure(text=f"{self.voice_phrase_limit_var.get():.1f} sn")
        self._update_action_help()
        self._update_mode_help()
        self._apply_selected_theme()
        self._persist_settings_if_ready()

    def _persist_settings_if_ready(self) -> None:
        if self._loading_state or not self._persist_ready:
            return
        try:
            self.store.save_settings(self.state)
        except Exception as exc:
            self.log(f"Ayarlar kaydedilemedi: {exc}")

    def _apply_selected_theme(self, force: bool = False) -> None:
        palette = THEME_PALETTES.get(self.state.ui.theme, THEME_PALETTES["Neon Gece"])
        if (palette == self.palette) and (not force):
            return
        self.palette = palette
        self._safe_config(self.root, fg_color=self.palette["bg"])
        self._safe_config(self.main, fg_color=self.palette["bg"])

        self._safe_config(self.title_label, text_color=self.palette["text"])
        self._safe_config(self.subtitle_label, text_color=self.palette["muted"])

        self._safe_config(self.tabview, fg_color=self.palette["surface"])
        self._safe_config(
            self.tabview,
            segmented_button_fg_color=self.palette["surface_alt"],
            segmented_button_selected_color=self.palette["accent"],
            segmented_button_selected_hover_color=self.palette["accent_hover"],
            segmented_button_unselected_color=self.palette["surface_alt"],
            segmented_button_unselected_hover_color=self.palette["input"],
            text_color=self.palette["text"],
        )

        for card in self.cards:
            self._safe_config(card, fg_color=self.palette["surface"], border_color=self.palette["surface_alt"])

        self._safe_config(self.start_btn, fg_color=self.palette["success"], hover_color=self.palette["success_hover"], text_color=self.palette["text"])
        self._safe_config(self.stop_btn, fg_color=self.palette["danger"], hover_color=self.palette["danger_hover"], text_color=self.palette["text"])
        self._safe_config(self.test_btn, fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], text_color=self.palette["text"])
        self._safe_config(self.status_chip, fg_color=self.palette["surface_alt"], text_color=self.palette["text"], corner_radius=10)

        for menu in (
            self.mode_menu,
            self.command_mode_menu,
            self.recognition_engine_menu,
            self.system_audio_filter_menu,
            self.action_menu,
            self.samplerate_menu,
        ):
            self._safe_config(
                menu,
                fg_color=self.palette["surface_alt"],
                button_color=self.palette["accent"],
                button_hover_color=self.palette["accent_hover"],
                text_color=self.palette["text"],
            )

        for entry in (
            self.voice_keyword_entry,
            self.vosk_model_entry,
            self.voice_level_entry,
            self.custom_command_entry,
            self.required_entry,
            self.window_entry,
            self.min_gap_entry,
            self.cooldown_entry,
        ):
            self._safe_config(entry, fg_color=self.palette["input"], text_color=self.palette["text"], border_color=self.palette["surface_alt"])

        self._safe_config(self.threshold_slider, progress_color=self.palette["accent"], button_color=self.palette["accent"], button_hover_color=self.palette["accent_hover"])
        self._safe_config(self.voice_limit_slider, progress_color=self.palette["accent"], button_color=self.palette["accent"], button_hover_color=self.palette["accent_hover"])
        self._safe_config(self.mic_test_button, fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], text_color=self.palette["text"])
        self._safe_config(self.mic_test_bar, progress_color=self.palette["accent"], fg_color=self.palette["surface_alt"])

        self._safe_config(self.status_label, text_color=self.palette["text"])
        self._safe_config(self.log_text, fg_color=self.palette["input"], text_color=self.palette["text"], border_color=self.palette["surface_alt"])
        self._safe_config(self.command_showcase, fg_color=self.palette["input"], text_color=self.palette["text"], border_color=self.palette["surface_alt"])
        self._safe_config(self.scenario_showcase, fg_color=self.palette["input"], text_color=self.palette["text"], border_color=self.palette["surface_alt"])
        self._safe_config(self.tips_showcase, fg_color=self.palette["input"], text_color=self.palette["text"], border_color=self.palette["surface_alt"])
        self._safe_config(self.trigger_help_label, text_color=self.palette["muted"])
        self._safe_config(self.action_help_label, text_color=self.palette["muted"])

        self.bindings_tab.set_theme(self.palette)
        self.settings_tab.set_theme(self.palette)
        self.sistem_kontrol_tab_obj.set_theme(self.palette)
        self.senaryolar_tab_obj.set_theme(self.palette)
        self.pencere_tab_obj.set_theme(self.palette)
        self.akilli_ozellikler_tab.set_theme(self.palette)

    def _update_action_help(self) -> None:
        action = self._map_key(EYLEM_TURLERI, self.action_var.get().strip(), "uyku")
        self.custom_command_entry.configure(state="normal" if action == "ozel_komut" else "disabled")
        if action == "uyku":
            text = "Uyku Moduna Gec: bilgisayari uykuya alir"
        elif action == "kapat":
            text = "Bilgisayari Kapat: sistemi kapatir"
        else:
            text = "Ozel Komut Calistir: yazdiginiz komutu calistirir"
        self.action_help_label.configure(text=text)

    def _update_mode_help(self) -> None:
        mode = self._map_key(ALGILAMA_TURLERI, self.mode_var.get().strip(), "sesli_komut")
        is_voice = mode == "sesli_komut"
        is_offline = self._map_key(SES_MOTORLERI, self.recognition_engine_var.get().strip(), "cevrimici_whisper") == "cevrimdisi"

        voice_state = "normal" if is_voice else "disabled"
        clap_state = "normal" if not is_voice else "disabled"

        self.voice_keyword_entry.configure(state=voice_state)
        self.command_mode_menu.configure(state=voice_state)
        self.recognition_engine_menu.configure(state=voice_state)
        self.vosk_model_entry.configure(state="normal" if is_voice and is_offline else "disabled")
        self.voice_limit_slider.configure(state=voice_state)
        self.voice_level_entry.configure(state=voice_state)
        self.system_audio_filter_menu.configure(state=voice_state)

        self.threshold_slider.configure(state=clap_state)
        self.required_entry.configure(state=clap_state)
        self.window_entry.configure(state=clap_state)
        self.min_gap_entry.configure(state=clap_state)
        self.samplerate_menu.configure(state=clap_state)

        if is_voice and self._map_key(KOMUT_MODLARI, self.command_mode_var.get().strip(), "dogal") == "dogal":
            msg = "Dogal Komut: 'yarim saat sonra bilgisayari kapat', 'chrome ac', 'sesi kis', 'aktif pencereyi sola yasla'"
        elif is_voice:
            msg = "Anahtar Kelime: yalnizca belirttiginiz ifade gecerse"
        else:
            msg = "El Cirpma: hassasiyet ve sayiya gore tetikler"
        self.trigger_help_label.configure(text=msg)

    def refresh_app_list(self) -> None:
        self.available_apps = discover_installed_apps(limit=400)
        displays = [name for name, _ in self.available_apps]
        self.app_targets_by_display = {name: target for name, target in self.available_apps}
        self.bindings_tab.set_apps(self.available_apps)
        self.bindings_tab.set_info(f"{len(displays)} uygulama listelendi")

    def add_phrase_binding(self) -> None:
        app_display = self.bindings_tab.selected_app()
        phrase = self.bindings_tab.phrase()
        remove_phrase = self.bindings_tab.remove_phrase()
        if not phrase:
            self.bindings_tab.set_info("Komut cumlesi bos olamaz")
            return
        if not app_display or app_display.startswith("(uygulama"):
            self.bindings_tab.set_info("Gecerli bir uygulama secin")
            return

        target = self.app_targets_by_display.get(app_display, app_display)
        operation = self.bindings_tab.selected_operation()

        editing_phrase = self.bindings_tab.editing_phrase()
        update_mode = bool(editing_phrase) and normalize_text(remove_phrase) == normalize_text(editing_phrase)
        if update_mode and normalize_text(editing_phrase) != normalize_text(phrase):
            self.binding_store.remove(editing_phrase)

        ok, msg = self.binding_store.add(phrase, app_display, target, operation)
        if ok and update_mode:
            self.bindings_tab.set_info(f"Komut guncellendi: '{editing_phrase}' -> '{phrase}'")
        else:
            self.bindings_tab.set_info(msg)
        if ok:
            if not update_mode:
                self.bindings_tab.clear_phrase()
            self.bindings_tab.clear_editing_selection()
            self.refresh_bindings_preview()
            self._persist_bindings_if_ready()
            self.log(self.bindings_tab.info_var.get())

    def remove_phrase_binding(self) -> None:
        phrase = self.bindings_tab.remove_phrase()
        if not phrase:
            self.bindings_tab.set_info("Silmek icin komut cumlesi girin")
            return
        removed = self.binding_store.remove(phrase)
        if removed:
            self.bindings_tab.set_info(f"Silindi: {phrase}")
            self.bindings_tab.clear_remove_phrase()
            self.bindings_tab.clear_editing_selection()
            self.refresh_bindings_preview()
            self._persist_bindings_if_ready()
        else:
            self.bindings_tab.set_info("Eslesme bulunamadi")

    def _persist_bindings_if_ready(self) -> None:
        if self._loading_state or not self._persist_ready:
            return
        try:
            self.store.save_bindings(self.binding_store.all_items())
        except Exception as exc:
            self.log(f"Komut eslemeleri kaydedilemedi: {exc}")

    # ─── Custom phrases / scenario callbacks ─────────────────────────────────

    _SYSTEM_IDS: frozenset[str] = frozenset({
        "sesi_ac", "sesi_kis", "sesi_sessize_al",
        "parlaklik_arttir", "parlaklik_azalt",
        "ekrani_kilitle", "ekran_goruntusu", "cop_kutusu_ac",
        "wifi_ac", "wifi_kapat", "bluetooth_ac", "bluetooth_kapat",
    })
    _WINDOW_IDS: frozenset[str] = frozenset({
        "aktif_pencere_kucult", "aktif_pencere_buyut",
        "aktif_pencere_sola_yasla", "aktif_pencere_saga_yasla",
        "tum_pencereleri_kucult",
    })
    _TEST_DEFAULT_VALUES: dict[str, int] = {
        "sesi_ac": 6, "sesi_kis": 6,
        "parlaklik_arttir": 15, "parlaklik_azalt": 15,
    }

    def _init_custom_phrases(self) -> None:
        phrases = self.store.load_command_phrases()
        scenarios = self.store.load_scenarios()

        self.sistem_kontrol_tab_obj.load_phrases(
            {k: v for k, v in phrases.items() if k in self._SYSTEM_IDS}
        )
        self.pencere_tab_obj.load_phrases(
            {k: v for k, v in phrases.items() if k in self._WINDOW_IDS}
        )
        self.senaryolar_tab_obj.load_scenarios(scenarios)

        TurkishCommandParser.set_custom_phrases(phrases)
        TurkishCommandParser.set_custom_scenarios(scenarios)
        self.actions.update_scenarios(scenarios)
        self.log(f"Ozel ifadeler yuklendi: {len(phrases)} komut, {len(scenarios)} senaryo")

    def _test_system_action(self, command_id: str) -> None:
        val = self._TEST_DEFAULT_VALUES.get(command_id, 0)
        try:
            self.actions.execute_named_action(command_id, "sistem-test", value=val)
        except Exception as exc:
            self.log(f"Test hatasi ({command_id}): {exc}")

    def _save_system_phrases(self, phrases: dict[str, str]) -> None:
        try:
            all_phrases = self.store.load_command_phrases()
            all_phrases.update(phrases)
            self.store.save_command_phrases(all_phrases)
            TurkishCommandParser.set_custom_phrases(all_phrases)
            self.log("Sistem komut ifadeleri kaydedildi")
            self.sistem_kontrol_tab_obj.set_info("Kaydedildi ✓")
        except Exception as exc:
            self.log(f"Sistem ifadesi kayit hatasi: {exc}")

    def _save_scenarios(self, scenarios: list[dict]) -> None:
        try:
            self.store.save_scenarios(scenarios)
            TurkishCommandParser.set_custom_scenarios(scenarios)
            self.actions.update_scenarios(scenarios)
            self.log(f"Senaryolar kaydedildi ({len(scenarios)} adet)")
        except Exception as exc:
            self.log(f"Senaryo kayit hatasi: {exc}")

    def _test_scenario(self, scenario_id: str) -> None:
        try:
            self.actions.run_scenario(scenario_id, "senaryo-test")
        except Exception as exc:
            self.log(f"Senaryo test hatasi ({scenario_id}): {exc}")

    def _test_window_action(self, command_id: str) -> None:
        try:
            self.actions.execute_named_action(command_id, "pencere-test", value=0)
        except Exception as exc:
            self.log(f"Pencere test hatasi ({command_id}): {exc}")

    def _test_named_window_action(self, win_action: str, app_name: str) -> None:
        if not app_name:
            self.log("Uygulama adi bos olamaz")
            return
        try:
            self.actions.control_named_window(win_action, app_name, "pencere-test")
        except Exception as exc:
            self.log(f"Pencere islemi hatasi ({win_action} -> {app_name}): {exc}")

    def _save_window_phrases(self, phrases: dict[str, str]) -> None:
        try:
            all_phrases = self.store.load_command_phrases()
            all_phrases.update(phrases)
            self.store.save_command_phrases(all_phrases)
            TurkishCommandParser.set_custom_phrases(all_phrases)
            self.log("Pencere komut ifadeleri kaydedildi")
            self.pencere_tab_obj.set_info("Kaydedildi ✓")
        except Exception as exc:
            self.log(f"Pencere ifadesi kayit hatasi: {exc}")

    def save_all_to_db(self) -> None:
        self.sync_state()
        try:
            self.store.save_settings(self.state)
            self.store.save_bindings(self.binding_store.all_items())
            self._save_current_profile_snapshot()
            set_autostart(self.autostart_var.get())
            self.settings_tab.set_info("Ayarlar ve komutlar kaydedildi")
            self.log("SQLite: ayarlar ve komut eslemeleri kaydedildi")
        except Exception as exc:
            self.settings_tab.set_info("Kayit hatasi")
            messagebox.showerror("SQLite Hatasi", str(exc))

    def refresh_bindings_preview(self) -> None:
        items = self.binding_store.all_items()
        if not items:
            self.bindings_tab.set_bindings([])
            return
        rows = [(phrase, app, op) for phrase, app, _target, op in items]
        self.bindings_tab.set_bindings(rows)

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def start_monitoring(self) -> None:
        self.sync_state()
        if self.mic_monitor.running:
            self._stop_mic_test_ui(prompt_save=False)
            self.log("Mikrofon testi durduruldu.")

        try:
            if self.state.detection.mode == "sesli_komut":
                self.voice_detector.start()
            else:
                self.clap_detector.start()
        except Exception as exc:
            messagebox.showerror("Mikrofon Hatasi", str(exc))
            self.log(f"Mikrofon acilamadi: {exc}")
            return

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.set_status("Dinleniyor...")

    def stop_monitoring(self) -> None:
        self.clap_detector.stop()
        self.voice_detector.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.set_status("Durduruldu")

    def toggle_mic_test(self) -> None:
        if self.mic_monitor.running:
            self._stop_mic_test_ui()
            return

        if self.voice_detector.monitoring or self.clap_detector.monitoring:
            messagebox.showwarning("Mikrofon Testi", "Once dinlemeyi durdurun.")
            return

        self._start_mic_test_ui()

    def _start_mic_test_ui(self) -> None:
        if not self.mic_monitor.available:
            messagebox.showerror("Mikrofon Testi", "sounddevice gerekli")
            return

        samplerate = self.state.voice.samplerate if self.state.detection.mode == "sesli_komut" else self.state.detection.samplerate
        try:
            self.mic_monitor.start(samplerate)
        except Exception as exc:
            messagebox.showerror("Mikrofon Testi", str(exc))
            return

        self.mic_test_button.configure(text="Mikrofon Testini Durdur")
        self.mic_test_rate_var.set(f"Ornekleme: {samplerate} Hz")
        self.mic_test_status_var.set("Canli dinleme aktif")
        self._mic_test_db_samples.clear()
        self._mic_test_peak_samples.clear()
        self._mic_test_started_at = time.time()
        self._schedule_mic_poll()

    def _stop_mic_test_ui(self, prompt_save: bool = True) -> None:
        avg_db = self._average_or_default(self._mic_test_db_samples, -120.0)
        avg_peak = self._average_or_default(self._mic_test_peak_samples, 0.0)
        duration = max(0.0, time.time() - self._mic_test_started_at)

        self.mic_monitor.stop()
        if self.mic_test_after_id is not None:
            self.root.after_cancel(self.mic_test_after_id)
            self.mic_test_after_id = None
        self.mic_test_button.configure(text="Mikrofon Testini Baslat")
        self.mic_test_status_var.set("Hazir")
        self.mic_test_db_var.set("dBFS: -120.0")
        self.mic_test_peak_var.set("Peak: 0.00")
        self.mic_test_bar.set(0.0)

        if prompt_save and duration >= 1.5 and self._mic_test_db_samples:
            self._ask_save_mic_defaults(avg_db, avg_peak)

        self._mic_test_db_samples.clear()
        self._mic_test_peak_samples.clear()
        self._mic_test_started_at = 0.0

    def _schedule_mic_poll(self) -> None:
        self.mic_test_after_id = self.root.after(120, self._poll_mic_stats)

    def _poll_mic_stats(self) -> None:
        if not self.mic_monitor.running:
            return

        stats = self.mic_monitor.get_latest()
        dbfs = max(-120.0, min(0.0, stats.dbfs))
        level = (dbfs + 120.0) / 120.0
        self.mic_test_bar.set(level)
        self.mic_test_db_var.set(f"dBFS: {dbfs:.1f}")
        self.mic_test_peak_var.set(f"Peak: {stats.peak:.2f}")
        self.mic_test_status_var.set("Canli ses algilandi" if dbfs > -45.0 else "Dusuk ses / sessizlik")

        self._mic_test_db_samples.append(dbfs)
        self._mic_test_peak_samples.append(max(0.0, min(1.0, float(stats.peak))))
        if len(self._mic_test_db_samples) > 1800:
            self._mic_test_db_samples = self._mic_test_db_samples[-1800:]
        if len(self._mic_test_peak_samples) > 1800:
            self._mic_test_peak_samples = self._mic_test_peak_samples[-1800:]

        self._schedule_mic_poll()

    def _average_or_default(self, values: list[float], default: float) -> float:
        if not values:
            return default
        return float(sum(values) / len(values))

    def _ask_save_mic_defaults(self, avg_db: float, avg_peak: float) -> None:
        speech_samples = [v for v in self._mic_test_db_samples if v > -65.0]
        speech_db = self._average_or_default(speech_samples, avg_db)

        suggested_voice_level = int(max(200, min(3200, 1200 + (speech_db + 40.0) * 25.0)))
        suggested_threshold = float(max(0.30, min(0.95, avg_peak * 2.6)))

        msg = (
            "Mikrofon testi tamamlandi.\n\n"
            f"Ortalama ses: {avg_db:.1f} dBFS\n"
            f"Ortalama peak: {avg_peak:.2f}\n"
            f"Onerilen Ses Esigi: {suggested_voice_level}\n"
            f"Onerilen Clap Hassasiyet: {suggested_threshold:.2f}\n\n"
            "Bu canli degerler varsayilan ayar olarak kaydedilsin mi?"
        )

        if not messagebox.askyesno("Mikrofon Test Sonucu", msg):
            self.log("Mikrofon test degerleri kaydedilmedi")
            return

        self.voice_level_var.set(str(suggested_voice_level))
        self.threshold_var.set(suggested_threshold)
        self.sync_state()

        try:
            self.store.save_settings(self.state)
            self.settings_tab.set_info("Mikrofon test ayarlari varsayilan olarak kaydedildi")
            self.log("Mikrofon test ayarlari varsayilan olarak kaydedildi")
        except Exception as exc:
            self.settings_tab.set_info("Mikrofon test ayarlari kaydedilemedi")
            messagebox.showerror("Kayit Hatasi", str(exc))

    def on_audio_error(self, error: str) -> None:
        self.root.after(0, lambda: self.log(f"Ses hatasi: {error}"))

    def on_clap_event(self, peak: float, threshold: float, clap_count: int) -> None:
        def _update() -> None:
            self.log(f"El cirpma algilandi. Tepe={peak:.2f} Esik={threshold:.2f} Sayi={clap_count}")
            if clap_count >= self.state.detection.required_claps:
                self.execute_action("el cirpma")

        self.root.after(0, _update)

    def on_phrase_event(self, transcript: str, matched: bool) -> None:
        def _update() -> None:
            self.log(f"Algilanan cumle: {transcript}")

            plugin_result = self.plugin_manager.process_transcript(transcript)
            if plugin_result is not None:
                parsed = ParsedCommand(
                    action=str(plugin_result.get("action", "")),
                    app_name=str(plugin_result.get("target", "")),
                    value=int(plugin_result.get("value", 0) or 0),
                )
                if parsed.action:
                    self._run_parsed_command(parsed, "plugin")
                    return

            normalized = TurkishCommandParser.normalize(transcript)
            custom_binding = self.binding_store.match(transcript)
            if custom_binding is not None:
                app_display, target, operation = custom_binding
                if operation == "kapat":
                    ok, msg = close_application(target)
                else:
                    ok, msg = launch_application(target)
                    if ok:
                        self._last_app_context = target
                self.log(f"Komut eslesmesi: {app_display}")
                self.log(msg)
                self._log_history(transcript, f"binding:{operation}", ok, "binding")
                if not ok:
                    messagebox.showerror("Uygulama Hatasi", msg)
                return

            if self.state.voice.command_mode == "dogal":
                parsed = TurkishCommandParser.parse(transcript)
                if parsed.action == "bilinmiyor":
                    if normalized == "kapat" and self._last_app_context:
                        self._run_parsed_command(ParsedCommand(action="uygulama_kapat", app_name=self._last_app_context), "baglam")
                        return
                    return
                if parsed.delay_seconds > 0:
                    self._schedule_parsed_command(parsed)
                else:
                    self._run_parsed_command(parsed, "sesli komut")
                return

            if matched:
                self.log(f"Anahtar kelime eslesti: {self.state.voice.keyword}")
                self.execute_action("sesli komut")

        self.root.after(0, _update)

    def _schedule_parsed_command(self, parsed: ParsedCommand) -> None:
        if parsed.action == "uygulama_ac":
            description = f"uygulama ac ({parsed.app_name})"
        elif parsed.action == "uygulama_kapat":
            description = f"uygulama kapat ({parsed.app_name})"
        elif parsed.app_name:
            description = f"{parsed.action} ({parsed.app_name})"
        else:
            description = parsed.action
        self.scheduler.schedule(
            parsed.delay_seconds,
            description,
            lambda: self.root.after(0, lambda: self._run_parsed_command(parsed, "zamanlanmis komut")),
        )

    def _run_parsed_command(self, parsed: ParsedCommand, source: str) -> None:
        if self._should_confirm_risky(parsed.action):
            if not messagebox.askyesno("Guvenlik Onayi", f"'{parsed.action}' eylemi calistirilsin mi?"):
                return

        if parsed.action == "geri_al":
            try:
                self.actions.undo_last_action(source)
                self._log_history("geri al", "geri_al", True, source)
            except RuntimeError as exc:
                messagebox.showerror("Eylem Hatasi", str(exc))
                self._log_history("geri al", "geri_al", False, source)
            return

        if parsed.action == "uygulama_ac":
            ok, msg = launch_application(parsed.app_name)
            self.log(msg)
            if ok:
                self._last_app_context = parsed.app_name
            self._log_history(parsed.app_name, "uygulama_ac", ok, source)
            if not ok:
                messagebox.showerror("Uygulama Hatasi", msg)
            return

        if parsed.action == "uygulama_kapat":
            ok, msg = close_application(parsed.app_name)
            self.log(msg)
            self._log_history(parsed.app_name, "uygulama_kapat", ok, source)
            if not ok:
                messagebox.showerror("Uygulama Hatasi", msg)
            return

        if parsed.action == "yeniden_baslat":
            try:
                self.actions.restart(source)
                self._log_history("yeniden baslat", "yeniden_baslat", True, source)
            except RuntimeError as exc:
                messagebox.showerror("Eylem Hatasi", str(exc))
                self._log_history("yeniden baslat", "yeniden_baslat", False, source)
            return

        if parsed.action in {"uyku", "kapat"}:
            try:
                self.actions.run(ActionSettings(action=parsed.action), source)
                self._log_history(parsed.action, parsed.action, True, source)
            except RuntimeError as exc:
                messagebox.showerror("Eylem Hatasi", str(exc))
                self._log_history(parsed.action, parsed.action, False, source)
            return

        try:
            self.actions.execute_named_action(parsed.action, source, target=parsed.app_name, value=parsed.value)
            self._log_history(parsed.app_name or parsed.action, parsed.action, True, source)
            self._maybe_suggest_routine()
        except RuntimeError as exc:
            messagebox.showerror("Eylem Hatasi", str(exc))
            self._log_history(parsed.app_name or parsed.action, parsed.action, False, source)

    def test_selected_action(self) -> None:
        if self.state.action.action in {"kapat", "ozel_komut"}:
            if not messagebox.askyesno("Onay", "Secili eylem test edilecek. Devam edilsin mi?"):
                return
        self.execute_action("manuel test")

    def execute_action(self, source: str) -> None:
        try:
            self.actions.run(self.state.action, source)
        except RuntimeError as exc:
            messagebox.showerror("Eylem Hatasi", str(exc))

    def on_close(self) -> None:
        try:
            self.save_all_to_db()
        except Exception:
            pass
        self.scheduler.cancel_all()
        self._stop_mic_test_ui(prompt_save=False)
        self.stop_monitoring()
        self.root.destroy()


def run() -> None:
    root = ctk.CTk()
    try:
        ico = icon_ico_path()
        if ico.exists():
            root.iconbitmap(default=str(ico))
        else:
            png = icon_png_path()
            if png.exists():
                icon = PhotoImage(file=str(png))
                root.iconphoto(True, icon)
                root._window_icon_ref = icon
    except Exception:
        pass
    app = AsistanApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
