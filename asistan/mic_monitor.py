from __future__ import annotations

import math
import threading
from dataclasses import dataclass

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None


@dataclass
class MicStats:
    rms: float = 0.0
    peak: float = 0.0
    dbfs: float = -120.0
    samplerate: int = 0


class MicrophoneMonitor:
    def __init__(self) -> None:
        self.stream = None
        self.running = False
        self._lock = threading.Lock()
        self._latest = MicStats()

    @property
    def available(self) -> bool:
        return sd is not None

    def start(self, samplerate: int) -> None:
        if not self.available:
            raise RuntimeError("sounddevice kurulu degil")
        if self.running:
            return

        self.stream = sd.InputStream(
            channels=1,
            samplerate=samplerate,
            dtype="float32",
            callback=self._callback,
            blocksize=1024,
        )
        self.stream.start()
        with self._lock:
            self._latest = MicStats(samplerate=samplerate)
        self.running = True

    def stop(self) -> None:
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        self.stream = None
        self.running = False

    def get_latest(self) -> MicStats:
        with self._lock:
            return MicStats(
                rms=self._latest.rms,
                peak=self._latest.peak,
                dbfs=self._latest.dbfs,
                samplerate=self._latest.samplerate,
            )

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            return

        signal = indata[:, 0]
        if signal.size == 0:
            return

        rms = float(np.sqrt(np.mean(np.square(signal))))
        peak = float(np.max(np.abs(signal)))
        dbfs = -120.0 if rms <= 1e-7 else float(20.0 * math.log10(rms))

        with self._lock:
            self._latest = MicStats(rms=rms, peak=peak, dbfs=dbfs, samplerate=self._latest.samplerate)
