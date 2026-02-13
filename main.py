"""GTK application entry point."""

from __future__ import annotations

from typing import Sequence

from orchestrator import Orchestrator


def main(argv: Sequence[str] | None = None) -> int:
    return Orchestrator().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
