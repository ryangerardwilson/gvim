"""File picker helpers."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Callable

from gi.repository import GLib

import document_io
from editor import launch_terminal_process


def begin_image_selector_o(start_dir: Path, on_pick: Callable[[Path], None]) -> bool:
    if shutil.which("o") is None:
        return False

    cache_path = get_o_picker_cache_path()
    if cache_path and cache_path.exists():
        try:
            cache_path.unlink()
        except OSError:
            pass

    cmd = [
        "o",
        "-p",
        start_dir.as_posix(),
        "-lf",
        "png,jpg,jpeg,gif,bmp,webp",
    ]

    if launch_terminal_process(cmd, cwd=start_dir) is None:
        return False

    if not cache_path:
        return False

    start_time = time.monotonic()
    _poll_for_o_picker_selection(cache_path, start_time, on_pick)
    return True


def begin_save_selector_o(start_dir: Path, on_pick: Callable[[Path], None]) -> bool:
    if shutil.which("o") is None:
        return False

    cache_path = get_o_picker_cache_path()
    if cache_path and cache_path.exists():
        try:
            cache_path.unlink()
        except OSError:
            pass

    cmd = ["o", "-s", start_dir.as_posix()]
    if launch_terminal_process(cmd, cwd=start_dir) is None:
        return False

    if not cache_path:
        return False

    start_time = time.monotonic()
    _poll_for_o_save_path(cache_path, start_time, on_pick)
    return True


def get_o_picker_cache_path() -> Path | None:
    cache_root = os.environ.get("XDG_CACHE_HOME")
    if cache_root:
        return Path(cache_root) / "o" / "picker-selection.txt"
    return Path.home() / ".cache" / "o" / "picker-selection.txt"


def _poll_for_o_picker_selection(
    cache_path: Path, start_time: float, on_pick: Callable[[Path], None]
) -> None:
    allowed_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

    def _check() -> bool:
        if cache_path.exists():
            try:
                data = cache_path.read_text(encoding="utf-8").strip()
            except OSError:
                return False
            if not data:
                return False
            first = data.splitlines()[0].strip()
            if not first:
                return False
            path = Path(first)
            if path.exists() and path.is_file():
                ext = path.suffix.lstrip(".").lower()
                if ext in allowed_exts:
                    on_pick(path)
            return False

        if time.monotonic() - start_time > 300:
            return False

        return True

    GLib.timeout_add(200, _check)


def _poll_for_o_save_path(
    cache_path: Path, start_time: float, on_pick: Callable[[Path], None]
) -> None:
    def _check() -> bool:
        if cache_path.exists():
            try:
                data = cache_path.read_text(encoding="utf-8").strip()
            except OSError:
                return False
            if not data:
                return False
            first = data.splitlines()[0].strip()
            if not first:
                return False
            path = document_io.coerce_docv_path(Path(first))
            on_pick(path)
            return False

        if time.monotonic() - start_time > 300:
            return False

        return True

    GLib.timeout_add(200, _check)
