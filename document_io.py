"""Document loading and saving helpers."""

from __future__ import annotations

from pathlib import Path

from block_model import BlockDocument
from persistence_text import load_document as load_text
from persistence_text import save_document as save_text


def load(path: Path) -> BlockDocument:
    return load_text(path)


def save(path: Path, document: BlockDocument) -> None:
    save_text(path, document)


def coerce_docv_path(path: Path) -> Path:
    if path.suffix == ".docv":
        return path
    return path.with_suffix(".docv")

