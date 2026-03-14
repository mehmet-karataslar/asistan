from __future__ import annotations

import time
import unicodedata
from dataclasses import replace
from typing import Callable

from .settings import VoiceSettings
from .speech_offline import OfflineSpeechEngine
from .speech_online import OnlineSpeechEngine


def normalize_text(value: str) -> str:
    lowered = value.casefold().strip()
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(char for char in normalized if not unicodedata.combining(char))


class VoiceKeywordDetector:
    def __init__(
        self,
        on_phrase: Callable[[str, bool], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.on_phrase = on_phrase
        self.on_error = on_error
        self.settings = VoiceSettings()
        self.last_trigger_time = 0.0

        self.online = OnlineSpeechEngine(self._handle_phrase, on_error)
        self.offline = OfflineSpeechEngine(self._handle_phrase, on_error)

    @property
    def available(self) -> bool:
        if self.settings.recognition_engine == "cevrimdisi":
            return self.offline.available
        return self.online.available

    @property
    def monitoring(self) -> bool:
        if self.settings.recognition_engine == "cevrimdisi":
            return self.offline.monitoring
        return self.online.monitoring

    def update_settings(self, settings: VoiceSettings) -> None:
        self.settings = replace(settings)
        self.online.update_settings(self.settings)
        self.offline.update_settings(self.settings)

    def start(self) -> None:
        self.last_trigger_time = 0.0
        if self.settings.recognition_engine == "cevrimdisi":
            self.offline.start()
            return
        self.online.start()

    def stop(self) -> None:
        self.online.stop()
        self.offline.stop()

    def _handle_phrase(self, transcript: str) -> None:
        matched = self._matches_keyword(transcript)
        if matched:
            now = time.time()
            if now - self.last_trigger_time < self.settings.cooldown:
                return
            self.last_trigger_time = now
        self.on_phrase(transcript, matched)

    def _matches_keyword(self, transcript: str) -> bool:
        keyword = normalize_text(self.settings.keyword)
        spoken = normalize_text(transcript)
        return bool(keyword) and keyword in spoken
