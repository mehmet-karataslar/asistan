from __future__ import annotations

import unicodedata


def normalize_text(value: str) -> str:
    lowered = value.casefold().strip()
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


class CommandBindingStore:
    def __init__(self) -> None:
        # normalized_phrase -> (original_phrase, app_display, app_target, operation)
        self._phrase_to_target: dict[str, tuple[str, str, str, str]] = {}

    def add(self, phrase: str, app_display: str, app_target: str, operation: str = "ac") -> tuple[bool, str]:
        phrase = phrase.strip()
        key = normalize_text(phrase)
        if not key:
            return False, "Komut cümlesi boş olamaz"
        op = operation if operation in {"ac", "kapat"} else "ac"
        self._phrase_to_target[key] = (phrase, app_display, app_target, op)
        op_label = "ac" if op == "ac" else "kapat"
        return True, f"Komut kaydedildi: '{phrase}' -> {app_display} ({op_label})"

    def clear(self) -> None:
        self._phrase_to_target.clear()

    def load_items(self, rows: list[tuple[str, str, str, str]]) -> None:
        self.clear()
        for phrase, app_display, app_target, operation in rows:
            self.add(phrase, app_display, app_target, operation)

    def remove(self, phrase: str) -> bool:
        key = normalize_text(phrase)
        return self._phrase_to_target.pop(key, None) is not None

    def match(self, transcript: str) -> tuple[str, str, str] | None:
        spoken = normalize_text(transcript)
        for phrase_key, payload in self._phrase_to_target.items():
            if phrase_key and phrase_key in spoken:
                _original, app_display, app_target, operation = payload
                return app_display, app_target, operation
        return None

    def all_items(self) -> list[tuple[str, str, str, str]]:
        rows: list[tuple[str, str, str, str]] = []
        for _phrase_key, (original_phrase, app_display, app_target, operation) in self._phrase_to_target.items():
            rows.append((original_phrase, app_display, app_target, operation))
        rows.sort(key=lambda row: row[0])
        return rows
