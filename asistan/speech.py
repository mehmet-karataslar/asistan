from __future__ import annotations

import threading
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
        self._phrase_lock = threading.Lock()
        self._pending_fragments: list[str] = []
        self._pending_timer: threading.Timer | None = None
        self._flush_delay = 0.55

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
        self._flush_delay = max(0.35, min(0.9, self.settings.phrase_time_limit * 0.22))
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
        self._flush_pending_phrase()

    def _handle_phrase(self, transcript: str) -> None:
        cleaned = transcript.strip()
        if not cleaned:
            return
        with self._phrase_lock:
            self._pending_fragments.append(cleaned)
            if self._pending_timer is not None:
                self._pending_timer.cancel()
            self._pending_timer = threading.Timer(self._flush_delay, self._flush_pending_phrase)
            self._pending_timer.daemon = True
            self._pending_timer.start()

    def _flush_pending_phrase(self) -> None:
        with self._phrase_lock:
            timer = self._pending_timer
            self._pending_timer = None
            fragments = self._pending_fragments[:]
            self._pending_fragments.clear()

        if timer is not None:
            timer.cancel()
        if not fragments:
            return

        merged_parts: list[str] = []
        last_norm = ""
        for fragment in fragments:
            part = fragment.strip()
            if not part:
                continue
            current_norm = normalize_text(part)
            if current_norm and current_norm == last_norm:
                continue
            merged_parts.append(part)
            if current_norm:
                last_norm = current_norm

        transcript = " ".join(merged_parts).strip()
        if not transcript:
            return

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
