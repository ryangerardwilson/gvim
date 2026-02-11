"""Visual-mode key handling."""
from __future__ import annotations

from collections.abc import Callable


def handle_key(key_name: str, on_mode_change: Callable[[str], None]) -> bool:
    if key_name == "Escape":
        on_mode_change("normal")
        return True
    if key_name == "v":
        on_mode_change("normal")
        return True
    return False
