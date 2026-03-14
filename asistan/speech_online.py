from __future__ import annotations

import threading
import time
from dataclasses import replace
from typing import Callable

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

from .settings import VoiceSettings


class OnlineSpeechEngine:
    def __init__(self, on_phrase: Callable[[str], None], on_error: Callable[[str], None]) -> None:
        self.on_phrase = on_phrase
        self.on_error = on_error
        self.settings = VoiceSettings()
        self.monitoring = False
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.recognizer = sr.Recognizer() if sr is not None else None

    @property
    def available(self) -> bool:
        return sd is not None and sr is not None and self.recognizer is not None

    def update_settings(self, settings: VoiceSettings) -> None:
        self.settings = replace(settings)

    def start(self) -> None:
        if not self.available:
            raise RuntimeError("Cevrimici ses tanima icin SpeechRecognition ve sounddevice gerekir")
        if self.monitoring:
            return

        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        self.monitoring = True

    def stop(self) -> None:
        self.stop_event.set()
        self.monitoring = False

    def _loop(self) -> None:
        samplerate = self.settings.samplerate
        frames_per_phrase = max(1, int(self.settings.phrase_time_limit * samplerate))

        while not self.stop_event.is_set():
            try:
                audio = sd.rec(frames_per_phrase, samplerate=samplerate, channels=1, dtype="int16")
                sd.wait()
                if self.stop_event.is_set():
                    break

                flattened = np.squeeze(audio)
                if flattened.size == 0:
                    continue

                peak = int(np.max(np.abs(flattened)))
                if peak < self.settings.min_voice_level:
                    continue

                audio_data = sr.AudioData(flattened.tobytes(), samplerate, 2)
                transcript = self.recognizer.recognize_google(audio_data, language="tr-TR")
                if transcript.strip():
                    self.on_phrase(transcript)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                self.on_error(f"Cevrimici ses tanima hatasi: {exc}")
                time.sleep(2)
            except Exception as exc:
                self.on_error(str(exc))
                time.sleep(1)

        self.monitoring = False
