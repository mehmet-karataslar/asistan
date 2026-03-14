from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    action: str
    delay_seconds: int = 0
    app_name: str = ""
    value: int = 0


class TurkishCommandParser:
    _SCENARIOS = {
        "ders modu": "ders_modu",
        "is modu": "is_modu",
        "oyun modu": "oyun_modu",
        "toplanti modu": "toplanti_modu",
        "gece modu": "gece_modu",
    }

    _CUSTOM_PHRASES: dict[str, tuple[str, ...]] = {}
    _CUSTOM_SCENARIOS: dict[str, str] = {}

    _UNITS = {
        "saniye": 1,
        "sn": 1,
        "dakika": 60,
        "dk": 60,
        "saat": 3600,
    }

    # ─ Kulınıcı tarafından özelleştirilebilir ifadeler ─────────────────────────────────
    _custom_phrases: dict[str, str] = {}    # komut_id -> normalize edilmiş ifade
    _custom_scenarios: list[dict] = []       # senaryo dict listesi

    # Numerik değer gerektiren komutlar
    _ACTIONS_WITH_VALUE: frozenset[str] = frozenset({
        "sesi_ac", "sesi_kis", "parlaklik_arttir", "parlaklik_azalt"
    })
    _ACTION_DEFAULT_VALUES: dict[str, int] = {
        "sesi_ac": 6, "sesi_kis": 6,
        "parlaklik_arttir": 15, "parlaklik_azalt": 15,
    }

    @classmethod
    def set_custom_phrases(cls, phrases: dict[str, str]) -> None:
        """Normalize ederek sakla – main_window DB yüklemesi sırasında çağrılır."""
        cls._custom_phrases = {
            k: cls.normalize(v) for k, v in phrases.items() if v.strip()
        }

    @classmethod
    def set_custom_scenarios(cls, scenarios: list[dict]) -> None:
        """Senaryo listesini sakla."""
        cls._custom_scenarios = list(scenarios)

    @classmethod
    def _check_custom_scenarios(cls, value: str, delay: int) -> "ParsedCommand | None":
        for sc in cls._custom_scenarios:
            phrase = cls.normalize(sc.get("trigger_phrase", ""))
            if phrase and phrase in value:
                return ParsedCommand(
                    action="senaryo_calistir",
                    app_name=sc["id"],
                    delay_seconds=delay,
                )
        return None

    @classmethod
    def _check_custom_phrases(cls, value: str, delay: int) -> "ParsedCommand | None":
        for command_id, phrase in cls._custom_phrases.items():
            if phrase and phrase in value:
                if command_id in cls._ACTIONS_WITH_VALUE:
                    amt = cls._extract_amount(value, cls._ACTION_DEFAULT_VALUES.get(command_id, 0))
                    return ParsedCommand(action=command_id, value=amt, delay_seconds=delay)
                return ParsedCommand(action=command_id, delay_seconds=delay)
        return None

    @staticmethod
    def normalize(text: str) -> str:
        lowered = text.casefold().strip()
        normalized = unicodedata.normalize("NFKD", lowered)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    @classmethod
    def set_custom_phrases(cls, phrases: dict[str, str]) -> None:
        normalized: dict[str, tuple[str, ...]] = {}
        for command_id, raw_value in phrases.items():
            items = [cls.normalize(part) for part in str(raw_value).split(",")]
            filtered = tuple(item for item in items if item)
            if filtered:
                normalized[command_id] = filtered
        cls._CUSTOM_PHRASES = normalized

    @classmethod
    def set_custom_scenarios(cls, scenarios: list[dict]) -> None:
        normalized: dict[str, str] = {}
        for scenario in scenarios:
            scenario_id = str(scenario.get("id", "")).strip()
            trigger_phrase = cls.normalize(str(scenario.get("trigger_phrase", "")))
            if scenario_id and trigger_phrase:
                normalized[trigger_phrase] = scenario_id
        cls._CUSTOM_SCENARIOS = normalized

    @classmethod
    def _phrases_for(cls, command_id: str, *defaults: str) -> tuple[str, ...]:
        custom = cls._CUSTOM_PHRASES.get(command_id)
        if custom:
            return custom
        return tuple(cls.normalize(item) for item in defaults if item)

    @classmethod
    def _contains_any(cls, value: str, command_id: str, *defaults: str) -> bool:
        return any(phrase and phrase in value for phrase in cls._phrases_for(command_id, *defaults))

    @classmethod
    def parse(cls, text: str) -> ParsedCommand:
        value = cls.normalize(text)

        delay = cls._parse_delay(value)

        # ─ Önce özel senaryo ifadelerini kontrol et ──────────────────────────────────
        if cls._custom_scenarios:
            custom_sc = cls._check_custom_scenarios(value, delay)
            if custom_sc:
                return custom_sc
        else:
            scenario = cls._parse_scenario(value)
            if scenario:
                return ParsedCommand(action="senaryo_calistir", app_name=scenario, delay_seconds=delay)

        # ─ Özel komut ifade kontrolü ──────────────────────────────────────────
        if cls._custom_phrases:
            custom_cmd = cls._check_custom_phrases(value, delay)
            if custom_cmd:
                return custom_cmd

        # ─ Varsayılan ayrıştırma mantığı ─────────────────────────────────────────

        if "yeniden baslat" in value or "restart" in value:
            return ParsedCommand(action="yeniden_baslat", delay_seconds=delay)

        if "uyku" in value or "uykuya gec" in value:
            return ParsedCommand(action="uyku", delay_seconds=delay)

        if "bilgisayar" in value and "kapat" in value:
            return ParsedCommand(action="kapat", delay_seconds=delay)

        if cls._contains_any(value, "ekrani_kilitle", "ekrani kilitle", "bilgisayari kilitle"):
            return ParsedCommand(action="ekrani_kilitle", delay_seconds=delay)

        if cls._contains_any(value, "ekran_goruntusu", "ekran goruntusu al", "ekran resmi al", "ss al"):
            return ParsedCommand(action="ekran_goruntusu", delay_seconds=delay)

        if cls._contains_any(value, "cop_kutusu_ac", "cop kutusunu ac", "geri donusum kutusunu ac"):
            return ParsedCommand(action="cop_kutusu_ac", delay_seconds=delay)

        volume_command = cls._parse_volume(value)
        if volume_command is not None:
            return ParsedCommand(action=volume_command[0], value=volume_command[1], delay_seconds=delay)

        brightness_command = cls._parse_brightness(value)
        if brightness_command is not None:
            return ParsedCommand(action=brightness_command[0], value=brightness_command[1], delay_seconds=delay)

        network_command = cls._parse_network(value)
        if network_command is not None:
            return ParsedCommand(action=network_command, delay_seconds=delay)

        window_command = cls._parse_window_command(value)
        if window_command is not None:
            return ParsedCommand(action=window_command[0], app_name=window_command[1], delay_seconds=delay)

        active_window_command = cls._parse_active_window_command(value)
        if active_window_command is not None:
            return ParsedCommand(action=active_window_command, delay_seconds=delay)

        if cls._contains_any(value, "tum_pencereleri_kucult", "tum pencereleri kucult", "tum pencereleri asagi al"):
            return ParsedCommand(action="tum_pencereleri_kucult", delay_seconds=delay)

        app_to_close = cls._parse_close_app(value)
        if app_to_close:
            return ParsedCommand(action="uygulama_kapat", app_name=app_to_close, delay_seconds=delay)

        if "kapat" in value:
            return ParsedCommand(action="kapat", delay_seconds=delay)

        app_name = cls._parse_open_app(value)
        if app_name:
            return ParsedCommand(action="uygulama_ac", app_name=app_name, delay_seconds=delay)

        return ParsedCommand(action="bilinmiyor", delay_seconds=delay)

    @classmethod
    def _parse_delay(cls, value: str) -> int:
        if "yarim saat" in value or "yarim saat sonra" in value:
            return 30 * 60

        match = re.search(r"(\d+)\s*(saniye|sn|dakika|dk|saat)\s*sonra", value)
        if not match:
            return 0

        amount = int(match.group(1))
        unit = match.group(2)
        return amount * cls._UNITS.get(unit, 0)

    @staticmethod
    def _parse_open_app(value: str) -> str:
        # ornek: "chrome ac" "spotify ac" "discord ac"
        match = re.search(r"([a-z0-9_.\-']+)\s+ac", value)
        if not match:
            return ""
        return TurkishCommandParser._clean_target(match.group(1))

    @staticmethod
    def _parse_close_app(value: str) -> str:
        # ornek: "chrome kapat" "discord uygulamasini kapat"
        match = re.search(r"([a-z0-9_.\-']+)\s+(uygulamasini\s+)?kapat", value)
        if not match:
            return ""
        candidate = TurkishCommandParser._clean_target(match.group(1))
        if candidate in {"bilgisayar", "sistem"}:
            return ""
        return candidate

    @classmethod
    def _parse_scenario(cls, value: str) -> str:
        for spoken, scenario in cls._CUSTOM_SCENARIOS.items():
            if spoken in value:
                return scenario
        for spoken, scenario in cls._SCENARIOS.items():
            if spoken in value:
                return scenario
        return ""

    @staticmethod
    def _extract_amount(value: str, default: int) -> int:
        match = re.search(r"(\d+)", value)
        if not match:
            return default
        return int(match.group(1))

    @classmethod
    def _parse_volume(cls, value: str) -> tuple[str, int] | None:
        if cls._contains_any(value, "sesi_sessize_al", "sessize al", "sesi kapat"):
            return "sesi_sessize_al", 0
        if cls._contains_any(value, "sesi_kis", "sesi azalt", "ses kis", "sesi kis"):
            return "sesi_kis", cls._extract_amount(value, 6)
        if cls._contains_any(value, "sesi_ac", "sesi arttir", "ses ac", "sesi yukelt"):
            return "sesi_ac", cls._extract_amount(value, 6)
        return None

    @classmethod
    def _parse_brightness(cls, value: str) -> tuple[str, int] | None:
        if cls._contains_any(value, "parlaklik_azalt", "parlakligi azalt", "parlaklik azalt", "parlaklik kis"):
            return "parlaklik_azalt", cls._extract_amount(value, 15)
        if cls._contains_any(value, "parlaklik_arttir", "parlakligi arttir", "parlaklik arttir", "parlakligi yukelt"):
            return "parlaklik_arttir", cls._extract_amount(value, 15)
        return None

    @staticmethod
    def _parse_network(value: str) -> str | None:
        if TurkishCommandParser._contains_any(value, "wifi_ac", "wifi ac", "wi fi ac", "kablosuz ac", "wlan ac"):
            return "wifi_ac"
        if TurkishCommandParser._contains_any(value, "wifi_kapat", "wifi kapat", "wi fi kapat", "kablosuz kapat", "wlan kapat"):
            return "wifi_kapat"
        if TurkishCommandParser._contains_any(value, "bluetooth_ac", "bluetooth ac"):
            return "bluetooth_ac"
        if TurkishCommandParser._contains_any(value, "bluetooth_kapat", "bluetooth kapat"):
            return "bluetooth_kapat"
        return None

    @staticmethod
    def _parse_window_command(value: str) -> tuple[str, str] | None:
        action_defaults = {
            "pencere_one_getir": ("one getir",),
            "pencere_kucult": ("kucult", "asagi al"),
            "pencere_buyut": ("buyut", "maximize et"),
            "pencere_sola_yasla": ("sola yasla",),
            "pencere_saga_yasla": ("saga yasla",),
        }
        for action, defaults in action_defaults.items():
            for phrase in TurkishCommandParser._phrases_for(action, *defaults):
                match = re.search(rf"(.+?)\s+({re.escape(phrase)})", value)
                if not match:
                    continue
                target = match.group(1).strip()
                target = re.sub(r"\b(uygulamayi|uygulamasini|pencereyi|penceresini)\b", "", target).strip()
                target = TurkishCommandParser._clean_target(target)
                if target in {"aktif", "aktif pencere", "tum", "tum pencereler"} or not target:
                    continue
                return action, target
        return None

    @staticmethod
    def _clean_target(target: str) -> str:
        value = target.strip().replace("'", "").replace("’", "")
        value = re.sub(r"(yi|yu|yı|yü|i|ı|u|ü)$", "", value)
        return value.strip()

    @staticmethod
    def _parse_active_window_command(value: str) -> str | None:
        if TurkishCommandParser._contains_any(value, "aktif_pencere_kucult", "aktif pencereyi kucult"):
            return "aktif_pencere_kucult"
        if TurkishCommandParser._contains_any(value, "aktif_pencere_buyut", "aktif pencereyi buyut"):
            return "aktif_pencere_buyut"
        if TurkishCommandParser._contains_any(value, "aktif_pencere_sola_yasla", "aktif pencereyi sola yasla"):
            return "aktif_pencere_sola_yasla"
        if TurkishCommandParser._contains_any(value, "aktif_pencere_saga_yasla", "aktif pencereyi saga yasla"):
            return "aktif_pencere_saga_yasla"
        return None
