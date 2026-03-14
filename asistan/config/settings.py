from __future__ import annotations

from dataclasses import dataclass, field


def default_system_phrases() -> dict[str, str]:
    return {
        "sesi_ac": "sesi arttir, ses ac, sesi yukelt",
        "sesi_kis": "sesi azalt, sesi kis, ses kis",
        "sesi_sessize_al": "sessize al, sesi kapat",
        "parlaklik_arttir": "parlakligi arttir, parlaklik arttir, parlakligi yukelt",
        "parlaklik_azalt": "parlakligi azalt, parlaklik azalt, parlaklik kis",
        "ekrani_kilitle": "ekrani kilitle, bilgisayari kilitle",
        "ekran_goruntusu": "ekran goruntusu al, ekran resmi al, ss al",
        "cop_kutusu_ac": "cop kutusunu ac, geri donusum kutusunu ac",
        "wifi_ac": "wifi ac, wi fi ac, kablosuz ac, wlan ac",
        "wifi_kapat": "wifi kapat, wi fi kapat, kablosuz kapat, wlan kapat",
        "bluetooth_ac": "bluetooth ac",
        "bluetooth_kapat": "bluetooth kapat",
    }


def default_scenario_phrases() -> dict[str, str]:
    return {
        "ders_modu": "ders modu",
        "is_modu": "is modu",
        "oyun_modu": "oyun modu",
        "toplanti_modu": "toplanti modu",
        "gece_modu": "gece modu",
    }


def default_scenario_steps() -> dict[str, str]:
    return {
        "ders_modu": "sessize al\nparlakligi azalt\ntum pencereleri kucult",
        "is_modu": "wifi ac\nparlakligi arttir\nsesi kis",
        "oyun_modu": "parlakligi arttir\nsesi arttir",
        "toplanti_modu": "sessize al\nparlakligi arttir",
        "gece_modu": "parlakligi azalt\nsesi kis",
    }


def default_window_phrases() -> dict[str, str]:
    return {
        "pencere_one_getir": "one getir",
        "pencere_kucult": "kucult, asagi al",
        "pencere_buyut": "buyut, maximize et",
        "pencere_sola_yasla": "sola yasla",
        "pencere_saga_yasla": "saga yasla",
        "aktif_pencere_kucult": "aktif pencereyi kucult",
        "aktif_pencere_buyut": "aktif pencereyi buyut",
        "aktif_pencere_sola_yasla": "aktif pencereyi sola yasla",
        "aktif_pencere_saga_yasla": "aktif pencereyi saga yasla",
        "tum_pencereleri_kucult": "tum pencereleri kucult, tum pencereleri asagi al",
    }


@dataclass
class DetectionSettings:
    mode: str = "sesli_komut"
    threshold: float = 0.82
    required_claps: int = 2
    window_seconds: float = 1.2
    min_clap_gap: float = 0.35
    cooldown: float = 10.0
    samplerate: int = 44100
    noise_multiplier: float = 6.5
    crest_threshold: float = 4.5


@dataclass
class ActionSettings:
    action: str = "uyku"
    custom_command: str = ""


@dataclass
class VoiceSettings:
    keyword: str = "bilgisayarı kapat"
    command_mode: str = "dogal"
    recognition_engine: str = "cevrimici"
    phrase_time_limit: float = 2.6
    samplerate: int = 16000
    cooldown: float = 8.0
    min_voice_level: int = 900
    vosk_model_path: str = ""
    filter_system_audio: bool = True


@dataclass
class UiSettings:
    theme: str = "Neon Gece"
    user_name: str = ""
    response_style: str = "samimi"
    security_level: str = "orta"
    learning_mode: bool = True
    active_profile: str = "varsayilan"


@dataclass
class AutomationSettings:
    system_phrases: dict[str, str] = field(default_factory=default_system_phrases)
    scenario_phrases: dict[str, str] = field(default_factory=default_scenario_phrases)
    scenario_steps: dict[str, str] = field(default_factory=default_scenario_steps)
    window_phrases: dict[str, str] = field(default_factory=default_window_phrases)


@dataclass
class AppState:
    detection: DetectionSettings = field(default_factory=DetectionSettings)
    action: ActionSettings = field(default_factory=ActionSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    ui: UiSettings = field(default_factory=UiSettings)
    automation: AutomationSettings = field(default_factory=AutomationSettings)
