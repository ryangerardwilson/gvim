from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from three_template import default_three_template


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class ImageBlock:
    path: str
    alt: str = ""
    data: bytes | None = None
    mime: str | None = None


@dataclass(frozen=True)
class ThreeBlock:
    source: str
    title: str = ""


Block = TextBlock | ImageBlock | ThreeBlock


class BlockDocument:
    def __init__(self, blocks: Sequence[Block], path: Path | None = None) -> None:
        self._blocks: List[Block] = list(blocks)
        self._path = path
        self._dirty = False

    @property
    def blocks(self) -> List[Block]:
        return self._blocks

    @property
    def path(self) -> Path | None:
        return self._path

    def set_path(self, path: Path | None) -> None:
        self._path = path

    @property
    def dirty(self) -> bool:
        return self._dirty

    def clear_dirty(self) -> None:
        self._dirty = False

    def append_block(self, block: Block) -> None:
        self._blocks.append(block)
        self._dirty = True

    def insert_block_after(self, index: int, block: Block) -> None:
        if index < 0:
            self._blocks.insert(0, block)
        elif index >= len(self._blocks) - 1:
            self._blocks.append(block)
        else:
            self._blocks.insert(index + 1, block)
        self._dirty = True

    def set_text_block(self, index: int, text: str) -> None:
        if index < 0 or index >= len(self._blocks):
            return
        block = self._blocks[index]
        if isinstance(block, TextBlock):
            self._blocks[index] = TextBlock(text)
            self._dirty = True

    def set_three_block(self, index: int, source: str) -> None:
        if index < 0 or index >= len(self._blocks):
            return
        block = self._blocks[index]
        if isinstance(block, ThreeBlock):
            self._blocks[index] = ThreeBlock(source, title=block.title)
            self._dirty = True


def sample_document(image_path: str | None) -> BlockDocument:
    blocks: List[Block] = [
        TextBlock(
            "# GTKV block editor\n"
            "Navigate blocks with j/k, open a text block with Enter.\n"
            "Text and images live in separate blocks.\n"
        )
    ]

    if image_path:
        blocks.append(ImageBlock(image_path, alt="Sample image"))

    blocks.extend(
        [
            TextBlock(
                "# Editing\n"
                "Enter opens a temp file in Vim inside your terminal.\n"
                "Exit Vim to refresh the block content.\n"
            ),
            TextBlock(
                "# Notes\n"
                "- Images are standalone blocks.\n"
                "- Vim runs externally; GTK stays focused on layout.\n"
            ),
            ThreeBlock(default_three_template()),
        ]
    )

    return BlockDocument(blocks)
