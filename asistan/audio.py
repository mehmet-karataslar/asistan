from __future__ import annotations

import queue
import threading
import time
from dataclasses import replace
from typing import Callable

import numpy as np

from .settings import DetectionSettings

try:
    import sounddevice as sd
except Exception:
    sd = None


class ClapDetector:
    def __init__(
        self,
        on_clap: Callable[[float, float, int], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.on_clap = on_clap
        self.on_error = on_error
        self.settings = DetectionSettings()
        self.monitoring = False
        self.audio_stream = None
        self.audio_queue: "queue.Queue[np.ndarray]" = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.last_trigger_time = 0.0
        self.last_clap_time = 0.0
        self.clap_times: list[float] = []
        self.noise_floor = 0.02

    @property
    def available(self) -> bool:
        return sd is not None

    def update_settings(self, settings: DetectionSettings) -> None:
        self.settings = replace(settings)

    def start(self) -> None:
        if not self.available:
            raise RuntimeError("sounddevice kutuphanesi kurulu degil")
        if self.monitoring:
            return

        self.stop_event.clear()
        self.clap_times.clear()
        self.last_clap_time = 0.0
        self.noise_floor = 0.02

        self.audio_stream = sd.InputStream(
            channels=1,
            samplerate=self.settings.samplerate,
            dtype="float32",
            callback=self._audio_callback,
            blocksize=1024,
        )
        self.audio_stream.start()

        self.worker_thread = threading.Thread(target=self._process_audio_loop, daemon=True)
        self.worker_thread.start()
        self.monitoring = True

    def stop(self) -> None:
        self.stop_event.set()
        if self.audio_stream is not None:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None
        self.monitoring = False

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self.audio_queue.put(np.array([], dtype=np.float32))
            return
        self.audio_queue.put(indata[:, 0].copy())

    def _process_audio_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=0.3)
            except queue.Empty:
                continue

            if chunk.size == 0:
                continue

            peak = float(np.max(np.abs(chunk)))
            rms = float(np.sqrt(np.mean(np.square(chunk))))
            if rms > 0:
                self.noise_floor = (self.noise_floor * 0.92) + (rms * 0.08)

            dynamic_threshold = max(self.settings.threshold, min(0.95, self.noise_floor * self.settings.noise_multiplier))
            crest_factor = peak / max(rms, 1e-6)

            if peak >= dynamic_threshold and crest_factor >= self.settings.crest_threshold:
                self._register_clap(peak, dynamic_threshold)

    def _register_clap(self, peak: float, dynamic_threshold: float) -> None:
        now = time.time()
        if now - self.last_trigger_time < self.settings.cooldown:
            return
        if now - self.last_clap_time < self.settings.min_clap_gap:
            return

        self.last_clap_time = now
        self.clap_times.append(now)
        self.clap_times = [value for value in self.clap_times if now - value <= self.settings.window_seconds]

        clap_count = len(self.clap_times)
        if clap_count >= self.settings.required_claps:
            self.clap_times.clear()
            self.last_trigger_time = now

        self.on_clap(peak, dynamic_threshold, clap_count)
