"""Mode-specific key routing for editor input."""
from __future__ import annotations

from collections.abc import Callable

from editor_state import EditorState


class ModeRouter:
    def __init__(
        self,
        state: EditorState,
        on_mode_change: Callable[[str], None],
        on_inline_delete: Callable[[str], bool],
    ) -> None:
        self._state = state
        self._on_mode_change = on_mode_change
        self._on_inline_delete = on_inline_delete

    def handle_key(self, key_name: str) -> bool:
        if self._state.mode == "normal":
            if key_name == "i":
                self._on_mode_change("insert")
                return True
            if key_name == ":":
                # Placeholder for command-line mode.
                return True
            return False
        if self._state.mode == "insert":
            if key_name == "Escape":
                self._on_mode_change("normal")
                return True
            if key_name in {"BackSpace", "Delete"}:
                return self._on_inline_delete(key_name)
            return False
        return False
