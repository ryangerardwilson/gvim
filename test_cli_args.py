from cli_args import CliArgumentError, parse_args


def test_parse_open_file() -> None:
    options, gtk_args = parse_args(["notes.gvim"])

    assert options.command == "open"
    assert options.file == "notes.gvim"
    assert gtk_args == []


def test_parse_export_command() -> None:
    options, gtk_args = parse_args(["e"])

    assert options.command == "export"
    assert options.file is None
    assert gtk_args == []


def test_parse_quickstart_command_with_optional_file() -> None:
    options, gtk_args = parse_args(["q", "demo.gvim"])

    assert options.command == "quickstart"
    assert options.file == "demo.gvim"
    assert gtk_args == []


def test_legacy_export_flag_errors() -> None:
    try:
        parse_args(["-e"])
    except CliArgumentError as exc:
        assert str(exc) == "Use `gvim e` instead of `gvim -e`."
    else:
        raise AssertionError("Expected CliArgumentError")


def test_legacy_quickstart_flag_errors() -> None:
    try:
        parse_args(["-q"])
    except CliArgumentError as exc:
        assert str(exc) == "Use `gvim q [file.gvim]` instead of `gvim -q`."
    else:
        raise AssertionError("Expected CliArgumentError")
