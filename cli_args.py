"""Pure-stdlib CLI parsing for gvim."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Literal, Sequence

Command = Literal["open", "init", "export", "quickstart"]

USAGE_HINT = "Use `gvim [file.gvim]`, `gvim q [file.gvim]`, `gvim e`, or `gvim init`."


@dataclass(frozen=True, slots=True)
class CliOptions:
    command: Command
    file: str | None = None


class CliArgumentError(ValueError):
    """Raised when the user passes an invalid gvim CLI shape."""


def _reject_legacy_flags(argv: Sequence[str]) -> None:
    for arg in argv:
        if arg == "-e" or arg == "--export" or arg.startswith("--export="):
            raise CliArgumentError("Use `gvim e` instead of `gvim -e`.")
        if arg == "-q":
            raise CliArgumentError("Use `gvim q [file.gvim]` instead of `gvim -q`.")


def parse_args(argv: Sequence[str]) -> tuple[CliOptions, list[str]]:
    _reject_legacy_flags(argv)

    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("first", nargs="?")
    parser.add_argument("second", nargs="?")
    if hasattr(parser, "parse_known_intermixed_args"):
        args, gtk_args = parser.parse_known_intermixed_args(argv)
    else:
        args, gtk_args = parser.parse_known_args(argv)

    unexpected_positionals = [arg for arg in gtk_args if not arg.startswith("-")]
    if unexpected_positionals:
        raise CliArgumentError(USAGE_HINT)

    if args.first == "init":
        if args.second is not None:
            raise CliArgumentError("`gvim init` does not accept a file path.")
        return CliOptions(command="init"), gtk_args

    if args.first == "e":
        if args.second is not None:
            raise CliArgumentError("`gvim e` does not accept a file path.")
        return CliOptions(command="export"), gtk_args

    if args.first == "q":
        return CliOptions(command="quickstart", file=args.second), gtk_args

    if args.first is None:
        return CliOptions(command="open"), gtk_args

    if args.second is not None:
        raise CliArgumentError(USAGE_HINT)

    return CliOptions(command="open", file=args.first), gtk_args
