"""External editor orchestration."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from gi.repository import GLib


@dataclass
class EditorSession:
    process: subprocess.Popen
    path: Path
    index: int
    kind: str


def open_temp_editor(
    content: str, suffix: str, index: int, kind: str
) -> EditorSession | None:
    temp = tempfile.NamedTemporaryFile(
        prefix="gvim-block-", suffix=suffix, delete=False
    )
    temp_path = Path(temp.name)
    temp.write(content.encode("utf-8"))
    temp.flush()
    temp.close()

    editor_cmd = pick_terminal_editor()
    if not editor_cmd:
        return None

    process = launch_terminal_process(editor_cmd + [temp_path.as_posix()])
    if not process:
        return None

    return EditorSession(process=process, path=temp_path, index=index, kind=kind)


def schedule_editor_poll(
    session: EditorSession,
    on_update: Callable[[int, str, str], None],
    on_done: Callable[[], None],
) -> None:
    def _check() -> bool:
        if session.process.poll() is None:
            return True

        try:
            updated_text = session.path.read_text(encoding="utf-8")
        except OSError:
            updated_text = None
        if updated_text is not None:
            on_update(session.index, session.kind, updated_text)

        try:
            session.path.unlink()
        except OSError:
            pass

        on_done()
        return False

    GLib.timeout_add(250, _check)


def launch_terminal_process(
    command: list[str], cwd: Path | None = None
) -> subprocess.Popen | None:
    commands: list[list[str]] = []
    term_env = os.environ.get("TERMINAL")
    if term_env:
        commands.append(shlex.split(term_env))
    commands.extend(
        [
            [cmd]
            for cmd in (
                "alacritty",
                "foot",
                "kitty",
                "wezterm",
                "gnome-terminal",
                "xterm",
            )
        ]
    )

    cmd_joined = shlex.join(command)
    for cmd in commands:
        if not cmd:
            continue
        if shutil.which(cmd[0]) is None:
            continue
        launch_cmd = list(cmd)
        if any("{cmd}" in token for token in launch_cmd):
            launch_cmd = [token.replace("{cmd}", cmd_joined) for token in launch_cmd]
        else:
            launch_cmd.extend(["-e"] + command)
        try:
            process = subprocess.Popen(
                launch_cmd,
                cwd=cwd.as_posix() if cwd else None,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except OSError:
            continue
        return process
    return None


def pick_terminal_editor() -> list[str] | None:
    for cmd in ("nvim", "vim", "vi"):
        path = shutil.which(cmd)
        if path:
            return [path]
    return None
