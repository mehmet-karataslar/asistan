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

    _UNITS = {
        "saniye": 1,
        "sn": 1,
        "dakika": 60,
        "dk": 60,
        "saat": 3600,
    }

    @staticmethod
    def normalize(text: str) -> str:
        lowered = text.casefold().strip()
        normalized = unicodedata.normalize("NFKD", lowered)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    @classmethod
    def parse(cls, text: str) -> ParsedCommand:
        value = cls.normalize(text)

        delay = cls._parse_delay(value)

        scenario = cls._parse_scenario(value)
        if scenario:
            return ParsedCommand(action="senaryo_calistir", app_name=scenario, delay_seconds=delay)

        if "yeniden baslat" in value or "restart" in value:
            return ParsedCommand(action="yeniden_baslat", delay_seconds=delay)

        if "uyku" in value or "uykuya gec" in value:
            return ParsedCommand(action="uyku", delay_seconds=delay)

        if "bilgisayar" in value and "kapat" in value:
            return ParsedCommand(action="kapat", delay_seconds=delay)

        if "ekrani kilitle" in value or "bilgisayari kilitle" in value:
            return ParsedCommand(action="ekrani_kilitle", delay_seconds=delay)

        if "ekran goruntusu al" in value or "ekran resmi al" in value or value == "ss al":
            return ParsedCommand(action="ekran_goruntusu", delay_seconds=delay)

        if "cop kutusunu ac" in value or "geri donusum kutusunu ac" in value:
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

        if "tum pencereleri kucult" in value or "tum pencereleri asagi al" in value:
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
        if "sessize al" in value or "sesi kapat" in value:
            return "sesi_sessize_al", 0
        if "sesi azalt" in value or "ses kis" in value or "sesi kis" in value:
            return "sesi_kis", cls._extract_amount(value, 6)
        if "sesi arttir" in value or "ses ac" in value or "sesi yukelt" in value:
            return "sesi_ac", cls._extract_amount(value, 6)
        return None

    @classmethod
    def _parse_brightness(cls, value: str) -> tuple[str, int] | None:
        if "parlakligi azalt" in value or "parlaklik azalt" in value or "parlaklik kis" in value:
            return "parlaklik_azalt", cls._extract_amount(value, 15)
        if "parlakligi arttir" in value or "parlaklik arttir" in value or "parlakligi yukelt" in value:
            return "parlaklik_arttir", cls._extract_amount(value, 15)
        return None

    @staticmethod
    def _parse_network(value: str) -> str | None:
        if ("wifi" in value or "wi fi" in value or "kablosuz" in value or "wlan" in value) and "ac" in value:
            return "wifi_ac"
        if ("wifi" in value or "wi fi" in value or "kablosuz" in value or "wlan" in value) and "kapat" in value:
            return "wifi_kapat"
        if "bluetooth" in value and "ac" in value:
            return "bluetooth_ac"
        if "bluetooth" in value and "kapat" in value:
            return "bluetooth_kapat"
        return None

    @staticmethod
    def _parse_window_command(value: str) -> tuple[str, str] | None:
        patterns = {
            "pencere_one_getir": r"(.+?)\s+(one getir)",
            "pencere_kucult": r"(.+?)\s+(kucult|asagi al)",
            "pencere_buyut": r"(.+?)\s+(buyut|maximize et)",
            "pencere_sola_yasla": r"(.+?)\s+(sola yasla)",
            "pencere_saga_yasla": r"(.+?)\s+(saga yasla)",
        }
        for action, pattern in patterns.items():
            match = re.search(pattern, value)
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
        if "aktif pencereyi kucult" in value:
            return "aktif_pencere_kucult"
        if "aktif pencereyi buyut" in value:
            return "aktif_pencere_buyut"
        if "aktif pencereyi sola yasla" in value:
            return "aktif_pencere_sola_yasla"
        if "aktif pencereyi saga yasla" in value:
            return "aktif_pencere_saga_yasla"
        return None
