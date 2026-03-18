from io import StringIO
import sys
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
import main


def test_help_prints_human_written_text() -> None:
    with patch("sys.stdout", new=StringIO()) as stdout:
        code = main.main(["-h"])

    assert code == 0
    assert stdout.getvalue() == f"{main.HELP_TEXT.rstrip()}\n"


def test_app_spec_uses_single_version_source_and_config_path() -> None:
    assert main.APP_SPEC.app_name == "gvim"
    assert main.APP_SPEC.version == main.__version__
    assert main.APP_SPEC.no_args_mode == "dispatch"
    assert main.APP_SPEC.config_path_factory() == config.get_config_path()


def test_main_delegates_to_contract_runtime(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    def fake_run_app(spec, argv, dispatch):  # type: ignore[no-untyped-def]
        recorded["spec"] = spec
        recorded["argv"] = argv
        recorded["dispatch"] = dispatch
        return 0

    monkeypatch.setattr(main, "run_app", fake_run_app)

    rc = main.main(["notes.gvim"])

    assert rc == 0
    assert recorded["spec"] == main.APP_SPEC
    assert recorded["argv"] == ["notes.gvim"]
    assert recorded["dispatch"] is main._dispatch


def test_long_flag_aliases_map_to_contract_flags(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    def fake_run_app(spec, argv, dispatch):  # type: ignore[no-untyped-def]
        recorded["spec"] = spec
        recorded["argv"] = argv
        recorded["dispatch"] = dispatch
        return 0

    monkeypatch.setattr(main, "run_app", fake_run_app)

    rc = main.main(["--upgrade"])

    assert rc == 0
    assert recorded["spec"] == main.APP_SPEC
    assert recorded["argv"] == ["-u"]
    assert recorded["dispatch"] is main._dispatch


def test_install_script_prefers_machine_venv_provider() -> None:
    script = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert 'create_venv() {' in script
    assert 'virtualenv --python "$PYTHON_BIN" "$VENV_DIR"' in script
    assert '"$PYTHON_BIN" -m venv "$VENV_DIR"' in script
    assert '"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -r "${SOURCE_DIR}/requirements.txt"' in script
