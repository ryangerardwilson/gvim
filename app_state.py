"""Application state container."""

from __future__ import annotations

from dataclasses import dataclass

from block_model import Block, BlockDocument
from block_view import BlockEditorView
from editor import EditorSession


@dataclass
class AppState:
    document: BlockDocument | None = None
    view: BlockEditorView | None = None
    active_editor: EditorSession | None = None
    last_doc_key: int | None = None
    clipboard_block: Block | None = None
    clipboard_blocks: list[Block] | None = None
