from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class ImageBlock:
    path: str
    alt: str = ""


Block = TextBlock | ImageBlock


class BlockDocument:
    def __init__(self, blocks: Sequence[Block]) -> None:
        self._blocks: List[Block] = list(blocks)

    @property
    def blocks(self) -> List[Block]:
        return self._blocks

    def append_block(self, block: Block) -> None:
        self._blocks.append(block)

    def set_text_block(self, index: int, text: str) -> None:
        if index < 0 or index >= len(self._blocks):
            return
        block = self._blocks[index]
        if isinstance(block, TextBlock):
            self._blocks[index] = TextBlock(text)


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
        ]
    )

    return BlockDocument(blocks)
