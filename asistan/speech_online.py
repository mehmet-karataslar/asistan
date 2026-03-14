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

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None

from .settings import VoiceSettings
from .audio_filters import is_voice_like_int16


class OnlineSpeechEngine:
    def __init__(self, on_phrase: Callable[[str], None], on_error: Callable[[str], None]) -> None:
        self.on_phrase = on_phrase
        self.on_error = on_error
        self.settings = VoiceSettings()
        self.monitoring = False
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.recognizer = sr.Recognizer() if sr is not None else None
        self.whisper_model = None
        self._whisper_load_failed = False

    @property
    def available(self) -> bool:
        if sd is None:
            return False
        engine = (self.settings.recognition_engine or "cevrimici").strip()
        if engine == "cevrimici_whisper":
            return WhisperModel is not None or self.recognizer is not None
        return self.recognizer is not None

    def update_settings(self, settings: VoiceSettings) -> None:
        self.settings = replace(settings)

    def start(self) -> None:
        if not self.available:
            raise RuntimeError("Cevrimici ses tanima icin sounddevice ve bir ses motoru gerekir")
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
        chunk_seconds = 0.24
        silence_seconds = max(0.35, min(0.9, self.settings.phrase_time_limit * 0.22))
        max_phrase_seconds = max(1.8, self.settings.phrase_time_limit + 0.9)

        frames_per_chunk = max(1, int(chunk_seconds * samplerate))
        max_phrase_frames = max(1, int(max_phrase_seconds * samplerate))
        silence_limit_frames = max(1, int(silence_seconds * samplerate))
        continue_level = max(120, int(self.settings.min_voice_level * 0.55))

        speech_started = False
        silence_frames = 0
        collected_frames = 0
        collected_chunks: list[np.ndarray] = []

        def flush_phrase() -> None:
            nonlocal speech_started, silence_frames, collected_frames, collected_chunks
            if not collected_chunks:
                return
            try:
                merged = np.concatenate(collected_chunks)
                if merged.size < max(1, int(0.35 * samplerate)):
                    return
                transcript = self._transcribe_with_engine(merged, samplerate)
                if transcript.strip():
                    self.on_phrase(transcript)
            except Exception as exc:
                self.on_error(str(exc))
                time.sleep(1)
            finally:
                speech_started = False
                silence_frames = 0
                collected_frames = 0
                collected_chunks = []

        while not self.stop_event.is_set():
            try:
                audio = sd.rec(frames_per_chunk, samplerate=samplerate, channels=1, dtype="int16")
                sd.wait()
                if self.stop_event.is_set():
                    break

                flattened = np.squeeze(audio).astype(np.int16, copy=False)
                if flattened.size == 0:
                    continue
                if flattened.ndim != 1:
                    flattened = flattened.reshape(-1)

                voice_like = is_voice_like_int16(
                    flattened,
                    samplerate,
                    self.settings.min_voice_level,
                    filter_system_audio=self.settings.filter_system_audio,
                )
                peak_i16 = int(np.max(np.abs(flattened)))
                continue_voice = peak_i16 >= continue_level

                if voice_like:
                    speech_started = True
                    silence_frames = 0
                elif speech_started:
                    if continue_voice:
                        silence_frames = 0
                    else:
                        silence_frames += flattened.size
                else:
                    continue

                collected_chunks.append(flattened.copy())
                collected_frames += flattened.size

                if silence_frames >= silence_limit_frames or collected_frames >= max_phrase_frames:
                    flush_phrase()
            except Exception as exc:
                self.on_error(str(exc))
                time.sleep(1)

        flush_phrase()

        self.monitoring = False

    def _transcribe_with_engine(self, signal_i16: np.ndarray, samplerate: int) -> str:
        engine = (self.settings.recognition_engine or "cevrimici").strip()

        if engine == "cevrimici_whisper":
            text = self._transcribe_whisper(signal_i16, samplerate)
            if text:
                return text

        if self.recognizer is None:
            return ""
        try:
            audio_data = sr.AudioData(signal_i16.tobytes(), samplerate, 2)
            return self.recognizer.recognize_google(audio_data, language="tr-TR").strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            self.on_error(f"Cevrimici ses tanima hatasi: {exc}")
            time.sleep(1.0)
            return ""

    def _transcribe_whisper(self, signal_i16: np.ndarray, samplerate: int) -> str:
        model = self._get_whisper_model()
        if model is None:
            return ""

        audio = signal_i16.astype(np.float32) / 32768.0
        if samplerate != 16000:
            audio = self._resample_linear(audio, samplerate, 16000)

        try:
            segments, _info = model.transcribe(
                audio,
                language="tr",
                task="transcribe",
                vad_filter=True,
                beam_size=2,
                best_of=2,
                temperature=0.0,
                condition_on_previous_text=False,
            )
            pieces = [seg.text.strip() for seg in segments if getattr(seg, "text", "").strip()]
            return " ".join(pieces).strip()
        except Exception:
            return ""

    def _get_whisper_model(self):
        if WhisperModel is None or self._whisper_load_failed:
            return None
        if self.whisper_model is not None:
            return self.whisper_model

        model_names = ["small", "base"]
        for model_name in model_names:
            try:
                self.whisper_model = WhisperModel(model_name, device="cpu", compute_type="int8")
                return self.whisper_model
            except Exception:
                continue

        self._whisper_load_failed = True
        self.on_error("Whisper modeli yuklenemedi, Google motoruna geciliyor")
        return None

    @staticmethod
    def _resample_linear(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
        if src_rate == dst_rate or audio.size == 0:
            return audio
        ratio = float(dst_rate) / float(max(1, src_rate))
        target_len = max(1, int(round(audio.size * ratio)))
        src_idx = np.arange(audio.size, dtype=np.float32)
        dst_idx = np.linspace(0, max(0, audio.size - 1), num=target_len, dtype=np.float32)
        return np.interp(dst_idx, src_idx, audio).astype(np.float32, copy=False)
