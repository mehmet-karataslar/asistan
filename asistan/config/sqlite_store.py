from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .settings import ActionSettings, AppState, DetectionSettings, UiSettings, VoiceSettings

# ─── Varsayılan komut ifadeleri ──────────────────────────────────────────────
DEFAULT_COMMAND_PHRASES: dict[str, str] = {
    "sesi_ac":                  "sesi artır",
    "sesi_kis":                 "sesi kıs",
    "sesi_sessize_al":          "sessize al",
    "parlaklik_arttir":         "parlaklığı artır",
    "parlaklik_azalt":          "parlaklığı azalt",
    "ekrani_kilitle":           "ekranı kilitle",
    "ekran_goruntusu":          "ekran görüntüsü al",
    "cop_kutusu_ac":            "çöp kutusunu aç",
    "wifi_ac":                  "wifi aç",
    "wifi_kapat":               "wifi kapat",
    "bluetooth_ac":             "bluetooth aç",
    "bluetooth_kapat":          "bluetooth kapat",
    "aktif_pencere_kucult":     "aktif pencereyi küçült",
    "aktif_pencere_buyut":      "aktif pencereyi büyüt",
    "aktif_pencere_sola_yasla": "aktif pencereyi sola yasla",
    "aktif_pencere_saga_yasla": "aktif pencereyi sağa yasla",
    "tum_pencereleri_kucult":   "tüm pencereleri küçült",
}

# ─── Varsayılan senaryolar ────────────────────────────────────────────────────
DEFAULT_SCENARIOS: list[dict] = [
    {
        "id": "ders_modu",
        "display_name": "Ders Modu",
        "trigger_phrase": "ders modu",
        "steps": [
            {"action": "sesi_sessize_al", "value": 0},
            {"action": "parlaklik_azalt", "value": 15},
            {"action": "tum_pencereleri_kucult", "value": 0},
        ],
    },
    {
        "id": "is_modu",
        "display_name": "İş Modu",
        "trigger_phrase": "iş modu",
        "steps": [
            {"action": "wifi_ac", "value": 0},
            {"action": "parlaklik_arttir", "value": 10},
            {"action": "sesi_kis", "value": 4},
        ],
    },
    {
        "id": "oyun_modu",
        "display_name": "Oyun Modu",
        "trigger_phrase": "oyun modu",
        "steps": [
            {"action": "parlaklik_arttir", "value": 20},
            {"action": "sesi_ac", "value": 8},
        ],
    },
    {
        "id": "toplanti_modu",
        "display_name": "Toplantı Modu",
        "trigger_phrase": "toplantı modu",
        "steps": [
            {"action": "sesi_sessize_al", "value": 0},
            {"action": "parlaklik_arttir", "value": 5},
        ],
    },
    {
        "id": "gece_modu",
        "display_name": "Gece Modu",
        "trigger_phrase": "gece modu",
        "steps": [
            {"action": "parlaklik_azalt", "value": 25},
            {"action": "sesi_kis", "value": 8},
        ],
    },
]


class SQLiteStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bindings (
                    phrase TEXT PRIMARY KEY,
                    app_display TEXT NOT NULL,
                    app_target TEXT NOT NULL,
                    operation TEXT NOT NULL DEFAULT 'ac'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS command_phrases (
                    command_id TEXT PRIMARY KEY,
                    phrase TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scenarios (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    trigger_phrase TEXT NOT NULL,
                    steps TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_commands (
                    phrase TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL DEFAULT '',
                    value INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    action TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    source TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS routine_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_text TEXT NOT NULL,
                    accepted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._ensure_bindings_operation_column(conn)
            self._ensure_default_scenarios(conn)
            conn.commit()

    def load(self) -> tuple[AppState, list[tuple[str, str, str, str]]]:
        defaults = AppState()
        if not self.db_path.exists():
            return defaults, []

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            settings_map = {str(k): str(v) for k, v in rows}

            self._ensure_bindings_operation_column(conn)
            bindings = conn.execute(
                "SELECT phrase, app_display, app_target, operation FROM bindings ORDER BY phrase COLLATE NOCASE"
            ).fetchall()

        state = self._state_from_map(settings_map)
        normalized_bindings = [(str(p), str(d), str(t), str(op or "ac")) for p, d, t, op in bindings]
        return state, normalized_bindings

    def save_settings(self, state: AppState) -> None:
        settings_map = self._state_to_map(state)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM settings")
            conn.executemany(
                "INSERT INTO settings(key, value) VALUES(?, ?)",
                list(settings_map.items()),
            )
            conn.commit()

    def save_bindings(self, bindings: Iterable[tuple[str, str, str, str]]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_bindings_operation_column(conn)
            conn.execute("DELETE FROM bindings")
            conn.executemany(
                "INSERT INTO bindings(phrase, app_display, app_target, operation) VALUES(?, ?, ?, ?)",
                list(bindings),
            )
            conn.commit()

    def _ensure_bindings_operation_column(self, conn: sqlite3.Connection) -> None:
        columns = conn.execute("PRAGMA table_info(bindings)").fetchall()
        names = {str(col[1]).casefold() for col in columns}
        if "operation" not in names:
            conn.execute("ALTER TABLE bindings ADD COLUMN operation TEXT NOT NULL DEFAULT 'ac'")

    def _ensure_default_scenarios(self, conn: sqlite3.Connection) -> None:  # noqa: C901
        count = conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0]
        if count == 0:
            for sc in DEFAULT_SCENARIOS:
                conn.execute(
                    "INSERT OR IGNORE INTO scenarios(id, display_name, trigger_phrase, steps) VALUES(?, ?, ?, ?)",
                    (
                        sc["id"],
                        sc["display_name"],
                        sc["trigger_phrase"],
                        json.dumps(sc["steps"], ensure_ascii=False),
                    ),
                )

    # ─── Komut ifadeleri CRUD ─────────────────────────────────────────────────

    def load_command_phrases(self) -> dict[str, str]:
        """Returns merged dict: defaults overridden by any DB-stored custom phrases."""
        result: dict[str, str] = dict(DEFAULT_COMMAND_PHRASES)
        if not self.db_path.exists():
            return result
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute("SELECT command_id, phrase FROM command_phrases").fetchall()
                for cmd_id, phrase in rows:
                    result[str(cmd_id)] = str(phrase)
        except Exception:
            pass
        return result

    def save_command_phrases(self, phrases: dict[str, str]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM command_phrases")
            conn.executemany(
                "INSERT INTO command_phrases(command_id, phrase) VALUES(?, ?)",
                [(k, v) for k, v in phrases.items() if v.strip()],
            )
            conn.commit()

    # ─── Senaryolar CRUD ──────────────────────────────────────────────────────

    def load_scenarios(self) -> list[dict]:
        if not self.db_path.exists():
            return list(DEFAULT_SCENARIOS)
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    "SELECT id, display_name, trigger_phrase, steps FROM scenarios ORDER BY rowid"
                ).fetchall()
                if not rows:
                    return list(DEFAULT_SCENARIOS)
                result: list[dict] = []
                for sc_id, display_name, trigger_phrase, steps_json in rows:
                    try:
                        steps = json.loads(steps_json)
                    except Exception:
                        steps = []
                    result.append({
                        "id": str(sc_id),
                        "display_name": str(display_name),
                        "trigger_phrase": str(trigger_phrase),
                        "steps": steps,
                    })
                return result
        except Exception:
            return list(DEFAULT_SCENARIOS)

    def save_scenarios(self, scenarios: list[dict]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM scenarios")
            conn.executemany(
                "INSERT INTO scenarios(id, display_name, trigger_phrase, steps) VALUES(?, ?, ?, ?)",
                [
                    (
                        sc["id"],
                        sc["display_name"],
                        sc["trigger_phrase"],
                        json.dumps(sc["steps"], ensure_ascii=False),
                    )
                    for sc in scenarios
                ],
            )
            conn.commit()

    def load_learned_commands(self) -> list[tuple[str, str, str, int]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT phrase, action, target, value FROM learned_commands ORDER BY phrase COLLATE NOCASE"
            ).fetchall()
        return [(str(p), str(a), str(t), int(v)) for p, a, t, v in rows]

    def upsert_learned_command(self, phrase: str, action: str, target: str = "", value: int = 0) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO learned_commands(phrase, action, target, value) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(phrase) DO UPDATE SET action=excluded.action, target=excluded.target, value=excluded.value",
                (phrase, action, target, int(value)),
            )
            conn.commit()

    def save_history(self, transcript: str, action: str, success: bool, source: str = "") -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO command_history(ts, transcript, action, success, source) VALUES(datetime('now'), ?, ?, ?, ?)",
                (transcript, action, 1 if success else 0, source),
            )
            conn.commit()

    def load_history_summary(self, limit: int = 80) -> list[tuple[str, int, int]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT action, COUNT(*), SUM(success) FROM command_history GROUP BY action ORDER BY COUNT(*) DESC LIMIT ?",
                (max(5, int(limit)),),
            ).fetchall()
        return [(str(action), int(total or 0), int(ok or 0)) for action, total, ok in rows]

    def save_profile(self, profile_id: str, display_name: str, payload: dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO profiles(id, display_name, payload) VALUES(?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name, payload=excluded.payload",
                (profile_id, display_name, json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()

    def load_profiles(self) -> list[tuple[str, str, dict]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, display_name, payload FROM profiles ORDER BY id").fetchall()
        result: list[tuple[str, str, dict]] = []
        for pid, name, payload in rows:
            try:
                obj = json.loads(str(payload))
            except Exception:
                obj = {}
            result.append((str(pid), str(name), obj))
        return result

    def save_routine_suggestion(self, rule_text: str, accepted: bool = False) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO routine_suggestions(rule_text, accepted) VALUES(?, ?)",
                (rule_text, 1 if accepted else 0),
            )
            conn.commit()

    def load_routine_suggestions(self, limit: int = 20) -> list[tuple[int, str, bool]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, rule_text, accepted FROM routine_suggestions ORDER BY id DESC LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
        return [(int(i), str(t), bool(a)) for i, t, a in rows]

    def _state_to_map(self, state: AppState) -> dict[str, str]:
        return {
            "detection.mode": state.detection.mode,
            "detection.threshold": str(state.detection.threshold),
            "detection.required_claps": str(state.detection.required_claps),
            "detection.window_seconds": str(state.detection.window_seconds),
            "detection.min_clap_gap": str(state.detection.min_clap_gap),
            "detection.cooldown": str(state.detection.cooldown),
            "detection.samplerate": str(state.detection.samplerate),
            "detection.noise_multiplier": str(state.detection.noise_multiplier),
            "detection.crest_threshold": str(state.detection.crest_threshold),
            "action.action": state.action.action,
            "action.custom_command": state.action.custom_command,
            "voice.keyword": state.voice.keyword,
            "voice.command_mode": state.voice.command_mode,
            "voice.recognition_engine": state.voice.recognition_engine,
            "voice.phrase_time_limit": str(state.voice.phrase_time_limit),
            "voice.samplerate": str(state.voice.samplerate),
            "voice.cooldown": str(state.voice.cooldown),
            "voice.min_voice_level": str(state.voice.min_voice_level),
            "voice.vosk_model_path": state.voice.vosk_model_path,
            "ui.theme": state.ui.theme,
            "ui.user_name": state.ui.user_name,
            "ui.response_style": state.ui.response_style,
            "ui.security_level": state.ui.security_level,
            "ui.learning_mode": "1" if state.ui.learning_mode else "0",
            "ui.active_profile": state.ui.active_profile,
        }

    def _state_from_map(self, src: dict[str, str]) -> AppState:
        defaults = AppState()

        detection = DetectionSettings(
            mode=src.get("detection.mode", defaults.detection.mode),
            threshold=self._to_float(src.get("detection.threshold"), defaults.detection.threshold),
            required_claps=self._to_int(src.get("detection.required_claps"), defaults.detection.required_claps),
            window_seconds=self._to_float(src.get("detection.window_seconds"), defaults.detection.window_seconds),
            min_clap_gap=self._to_float(src.get("detection.min_clap_gap"), defaults.detection.min_clap_gap),
            cooldown=self._to_float(src.get("detection.cooldown"), defaults.detection.cooldown),
            samplerate=self._to_int(src.get("detection.samplerate"), defaults.detection.samplerate),
            noise_multiplier=self._to_float(src.get("detection.noise_multiplier"), defaults.detection.noise_multiplier),
            crest_threshold=self._to_float(src.get("detection.crest_threshold"), defaults.detection.crest_threshold),
        )

        action = ActionSettings(
            action=src.get("action.action", defaults.action.action),
            custom_command=src.get("action.custom_command", defaults.action.custom_command),
        )

        voice = VoiceSettings(
            keyword=src.get("voice.keyword", defaults.voice.keyword),
            command_mode=src.get("voice.command_mode", defaults.voice.command_mode),
            recognition_engine=src.get("voice.recognition_engine", defaults.voice.recognition_engine),
            phrase_time_limit=self._to_float(src.get("voice.phrase_time_limit"), defaults.voice.phrase_time_limit),
            samplerate=self._to_int(src.get("voice.samplerate"), defaults.voice.samplerate),
            cooldown=self._to_float(src.get("voice.cooldown"), defaults.voice.cooldown),
            min_voice_level=self._to_int(src.get("voice.min_voice_level"), defaults.voice.min_voice_level),
            vosk_model_path=src.get("voice.vosk_model_path", defaults.voice.vosk_model_path),
        )

        ui = UiSettings(
            theme=src.get("ui.theme", defaults.ui.theme),
            user_name=src.get("ui.user_name", defaults.ui.user_name),
            response_style=src.get("ui.response_style", defaults.ui.response_style),
            security_level=src.get("ui.security_level", defaults.ui.security_level),
            learning_mode=src.get("ui.learning_mode", "1") not in {"0", "false", "False"},
            active_profile=src.get("ui.active_profile", defaults.ui.active_profile),
        )

        return AppState(detection=detection, action=action, voice=voice, ui=ui)

    def _to_int(self, raw: str | None, fallback: int) -> int:
        try:
            return int(float(str(raw).strip().replace(",", ".")))
        except Exception:
            return fallback

    def _to_float(self, raw: str | None, fallback: float) -> float:
        try:
            return float(str(raw).strip().replace(",", "."))
        except Exception:
            return fallback
