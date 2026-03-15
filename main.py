#!/usr/bin/env python3
"""Contract-aware GTK application entry point."""

from __future__ import annotations

import faulthandler
import logging
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import IO, Sequence

import config
from _version import __version__

try:
    from rgw_cli_contract import AppSpec, resolve_install_script_path, run_app
except ModuleNotFoundError:
    contract_src = Path(__file__).resolve().parents[1] / "rgw_cli_contract" / "src"
    if not contract_src.exists():
        raise
    sys.path.insert(0, str(contract_src))
    from rgw_cli_contract import AppSpec, resolve_install_script_path, run_app


INSTALL_SCRIPT = resolve_install_script_path(__file__)
HELP_TEXT = """gvim

flags:
  gvim -h
    show this help
  gvim -v
    print the installed version
  gvim -u
    upgrade to the latest release
  gvim conf
    open the config in $VISUAL/$EDITOR

features:
  open a new or existing block-based GTK document
  # gvim [file.gvim]
  gvim
  gvim notes.gvim

  register the current directory as a vault root
  # gvim init
  gvim init

  export the current vault to static HTML
  # gvim e
  gvim e

  open a new file with quickstart demo content
  # gvim q [file.gvim]
  gvim q
  gvim q demo.gvim
"""


def _init_logging() -> tuple[Path, IO[str]]:
    log_path = Path.home() / ".gvim" / "gvim.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_stream = open(log_path, "a", buffering=1, encoding="utf-8")
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    faulthandler.enable(file=log_stream, all_threads=True)
    return log_path, log_stream


def _install_exception_hooks() -> None:
    def _log_excepthook(exc_type, exc_value, exc_tb):
        logging.error(
            "Uncaught exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    def _thread_excepthook(args):
        logging.error(
            "Unhandled thread exception in %s:\n%s",
            args.thread.name,
            "".join(
                traceback.format_exception(
                    args.exc_type, args.exc_value, args.exc_traceback
                )
            ),
        )

    sys.excepthook = _log_excepthook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_excepthook


def _dispatch(argv: list[str]) -> int:
    from orchestrator import Orchestrator

    log_path, _log_stream = _init_logging()
    _install_exception_hooks()
    logging.info("GVIM start")
    logging.info("Log file: %s", log_path)
    logging.info("Args: %s", list(argv) if argv is not None else sys.argv[1:])
    logging.info(
        "Env DISPLAY=%s WAYLAND_DISPLAY=%s",
        os.environ.get("DISPLAY"),
        os.environ.get("WAYLAND_DISPLAY"),
    )
    try:
        return Orchestrator().run(argv)
    except Exception:
        logging.error("Fatal error:\n%s", traceback.format_exc())
        raise


APP_SPEC = AppSpec(
    app_name="gvim",
    version=__version__,
    help_text=HELP_TEXT,
    install_script_path=INSTALL_SCRIPT,
    no_args_mode="dispatch",
    config_path_factory=config.get_config_path,
    config_bootstrap_text="{}\n",
)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--help"]:
        args = ["-h"]
    elif args == ["--version"]:
        args = ["-v"]
    elif args == ["--upgrade"]:
        args = ["-u"]
    return run_app(APP_SPEC, args, _dispatch)


if __name__ == "__main__":
    raise SystemExit(main())
