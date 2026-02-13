"""Document loading and saving helpers."""

from __future__ import annotations

from pathlib import Path

from block_model import BlockDocument
from persistence_sqlite import load_document, save_document


def load(path: Path) -> BlockDocument:
    return load_document(path)


def save(path: Path, document: BlockDocument) -> None:
    save_document(path, document)


def coerce_docv_path(path: Path) -> Path:
    if path.suffix == ".docv":
        return path
    return path.with_suffix(".docv")
