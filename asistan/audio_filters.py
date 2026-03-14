from __future__ import annotations

import numpy as np


def is_voice_like_int16(
    signal: np.ndarray,
    samplerate: int,
    min_level: int,
    *,
    filter_system_audio: bool,
) -> bool:
    """Simple microphone-focused gate to reduce speaker/music bleed.

    This is not full AEC, but it suppresses many non-speech/background segments.
    """
    if signal.size == 0:
        return False

    peak_i16 = int(np.max(np.abs(signal)))
    if peak_i16 < int(min_level):
        return False

    if not filter_system_audio:
        return True

    # Normalize to float -1..1
    x = signal.astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(np.square(x))))
    if rms < 0.0025:
        return False

    peak = float(np.max(np.abs(x)))
    crest = peak / max(rms, 1e-6)

    # Zero-crossing rate
    zcr = float(np.mean(np.abs(np.diff(np.signbit(x)))))

    # Frequency-domain speech ratio
    n = int(x.size)
    if n < 256:
        return False
    win = np.hanning(n)
    spec = np.fft.rfft(x * win)
    power = np.abs(spec) ** 2
    freqs = np.fft.rfftfreq(n, 1.0 / float(max(8000, samplerate)))

    total = float(np.sum(power) + 1e-9)
    speech = float(np.sum(power[(freqs >= 250) & (freqs <= 3800)]))
    low = float(np.sum(power[freqs < 180]))

    speech_ratio = speech / total
    low_ratio = low / total

    # Heuristics tuned for Turkish speech-like segments
    if speech_ratio < 0.33:
        return False
    if low_ratio > 0.60:
        return False
    if crest < 1.45:
        return False
    if not (0.01 <= zcr <= 0.30):
        return False

    return True
