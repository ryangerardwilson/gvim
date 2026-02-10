"""GTK application entry point."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Sequence

from config import AppConfig
from _version import __version__

INSTALL_SH_URL = "https://raw.githubusercontent.com/ryangerardwilson/gtkv/main/install.sh"
from orchestrator import Orchestrator


def parse_args(argv: Sequence[str]) -> AppConfig:
    parser = argparse.ArgumentParser(description="Vim-like GTK editor with image support")
    parser.add_argument("--theme", default="default", help="Theme name")
    parser.add_argument("--config", dest="config_path", help="Path to config file")
    parser.add_argument("--file-selector", default="o", help="File selector backend (o or gtk)")
    parser.add_argument("-c", dest="cleanup_cache", action="store_true", help="Clean cache and exit")
    parser.add_argument("-v", "--version", action="store_true", help="Show installed version")
    parser.add_argument("-u", "--upgrade", action="store_true", help="Upgrade to latest release")
    parser.add_argument("file", nargs="?", help="Optional file to open on startup")
    args = parser.parse_args(argv)
    return AppConfig(
        theme=args.theme,
        config_path=args.config_path,
        startup_file=args.file,
        file_selector=args.file_selector,
        cleanup_cache=args.cleanup_cache,
        show_version=args.version,
        upgrade=args.upgrade,
    )


def _config_path(config_override: str | None) -> str:
    if config_override:
        return config_override
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "gtkv", "config.json")


def _read_python_path(config_path: str) -> str | None:
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    value = data.get("python_path") if isinstance(data, dict) else None
    return value if isinstance(value, str) and value.strip() else None


def _write_python_path(config_path: str, python_path: str) -> None:
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    payload = {"python_path": python_path}
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def _python_supports_gtk4(python_path: str) -> bool:
    try:
        proc = subprocess.run(
            [python_path, "-c", "import gi; gi.require_version('Gtk','4.0')"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return proc.returncode == 0


def _ensure_python(config_path: str) -> None:
    configured = _read_python_path(config_path)
    if configured and os.path.abspath(configured) != os.path.abspath(sys.executable):
        os.execv(configured, [configured] + sys.argv)

    try:
        import gi  # type: ignore
        gi.require_version("Gtk", "4.0")
        return
    except ModuleNotFoundError:
        pass

    default_path = configured or sys.executable
    sys.stderr.write(
        "Missing PyGObject (gi). Provide a Python path with GTK4 + PyGObject.\n"
    )
    sys.stderr.flush()
    user_path = input(f"Python path [{default_path}]: ").strip() or default_path
    if not _python_supports_gtk4(user_path):
        sys.stderr.write("Selected Python cannot import GTK4 via gi.\n")
        sys.exit(1)
    _write_python_path(config_path, user_path)
    if os.path.abspath(user_path) != os.path.abspath(sys.executable):
        os.execv(user_path, [user_path] + sys.argv)


def _run_upgrade() -> int:
    try:
        curl = subprocess.Popen(
            ["curl", "-fsSL", INSTALL_SH_URL],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        print("Upgrade requires curl", file=sys.stderr)
        return 1

    try:
        bash = subprocess.Popen(["bash", "-s", "--", "-u"], stdin=curl.stdout)
        if curl.stdout is not None:
            curl.stdout.close()
    except FileNotFoundError:
        print("Upgrade requires bash", file=sys.stderr)
        curl.terminate()
        curl.wait()
        return 1

    bash_rc = bash.wait()
    curl_rc = curl.wait()

    if curl_rc != 0:
        stderr = (
            curl.stderr.read().decode("utf-8", errors="replace") if curl.stderr else ""
        )
        if stderr:
            sys.stderr.write(stderr)
        return curl_rc

    return bash_rc


def build_application(config: AppConfig):
    import gi  # type: ignore

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk  # type: ignore

    app = Gtk.Application(application_id="com.example.vimgtk")

    def on_activate(application) -> None:
        window = Gtk.ApplicationWindow(application=application)
        window.set_title("Vim GTK")
        window.set_default_size(1024, 768)

        orchestrator = Orchestrator(application=application, window=window, config=config)
        if getattr(config, "cleanup_cache", False):
            orchestrator.cleanup_cache()
            application.quit()
            return
        orchestrator.start()

        window.present()

    app.connect("activate", on_activate)
    return app


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    config = parse_args(args)
    config_path = _config_path(config.config_path)
    if config.show_version:
        print(__version__)
        return 0
    if config.upgrade:
        return _run_upgrade()
    _ensure_python(config_path)
    app = build_application(config)
    return app.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
