from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any


class PluginManager:
    def __init__(self, plugin_dir: Path) -> None:
        self.plugin_dir = plugin_dir
        self.plugins: list[ModuleType] = []

    def load_all(self) -> list[str]:
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.plugins.clear()
        loaded: list[str] = []
        for py_file in sorted(self.plugin_dir.glob("*.py")):
            name = f"asistan_plugin_{py_file.stem}"
            spec = spec_from_file_location(name, py_file)
            if spec is None or spec.loader is None:
                continue
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.plugins.append(mod)
            loaded.append(py_file.name)
        return loaded

    def process_transcript(self, transcript: str) -> dict[str, Any] | None:
        for plugin in self.plugins:
            hook = getattr(plugin, "on_transcript", None)
            if callable(hook):
                try:
                    result = hook(transcript)
                except Exception:
                    continue
                if isinstance(result, dict) and result.get("action"):
                    return result
        return None
