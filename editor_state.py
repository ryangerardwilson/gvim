"""Editor state for Vim-like mode handling."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class EditorState:
    """Minimal editor state placeholder for Vim-like mode handling."""

    mode: str = "normal"
    file_path: Optional[Path] = None
