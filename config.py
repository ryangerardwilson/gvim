"""User configuration helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "gtkv"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config: dict) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")


def get_python_path() -> str | None:
    config = load_config()
    value = config.get("python_path")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def set_python_path(python_path: str) -> None:
    config = load_config()
    config["python_path"] = python_path
    save_config(config)


def get_ui_mode() -> str | None:
    config = load_config()
    value = config.get("mode")
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return None


def set_ui_mode(mode: str) -> None:
    config = load_config()
    config["mode"] = mode
    save_config(config)


def get_vaults() -> list[Path]:
    config = load_config()
    value = config.get("vaults")
    if not isinstance(value, list):
        return []
    vaults: list[Path] = []
    for entry in value:
        if not isinstance(entry, str):
            continue
        if not entry.strip():
            continue
        vaults.append(Path(entry).expanduser())
    return vaults


def add_vault(vault_path: Path) -> bool:
    config = load_config()
    value = config.get("vaults")
    if isinstance(value, list):
        existing = [path for path in value if isinstance(path, str)]
    else:
        existing = []
    normalized = str(vault_path.expanduser().resolve())
    normalized_existing = {str(Path(path).expanduser().resolve()) for path in existing}
    if normalized in normalized_existing:
        return False
    existing.append(normalized)
    config["vaults"] = existing
    save_config(config)
    return True
