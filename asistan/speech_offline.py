from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from typing import Callable

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    from vosk import KaldiRecognizer, Model
except Exception:
    KaldiRecognizer = None
    Model = None

from .settings import VoiceSettings


class OfflineSpeechEngine:
    def __init__(self, on_phrase: Callable[[str], None], on_error: Callable[[str], None]) -> None:
        self.on_phrase = on_phrase
        self.on_error = on_error
        self.settings = VoiceSettings()
        self.monitoring = False
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.model = None

    @property
    def available(self) -> bool:
        return sd is not None and Model is not None and KaldiRecognizer is not None

    def update_settings(self, settings: VoiceSettings) -> None:
        self.settings = replace(settings)

    def start(self) -> None:
        if not self.available:
            raise RuntimeError("Cevrimdisi ses tanima icin vosk ve sounddevice gerekir")
        if not self.settings.vosk_model_path:
            raise RuntimeError("Cevrimdisi mod icin Vosk model yolu gerekli")
        if self.monitoring:
            return

        try:
            self.model = Model(self.settings.vosk_model_path)
        except Exception as exc:
            raise RuntimeError(f"Vosk modeli yuklenemedi: {exc}") from exc

        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        self.monitoring = True

    def stop(self) -> None:
        self.stop_event.set()
        self.monitoring = False

    def _loop(self) -> None:
        samplerate = self.settings.samplerate
        recognizer = KaldiRecognizer(self.model, samplerate)

        def callback(indata, frames, time_info, status):
            if status:
                return
            recognizer.AcceptWaveform(indata.tobytes())
            result = json.loads(recognizer.Result())
            text = (result.get("text") or "").strip()
            if text:
                self.on_phrase(text)

        try:
            with sd.RawInputStream(
                samplerate=samplerate,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=callback,
            ):
                while not self.stop_event.is_set():
                    time.sleep(0.1)
        except Exception as exc:
            self.on_error(f"Cevrimdisi ses tanima hatasi: {exc}")

        self.monitoring = False
