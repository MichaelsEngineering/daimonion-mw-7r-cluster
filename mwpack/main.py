"""Main CLI entrypoint with error mapping."""

from __future__ import annotations

import sys

from . import cli
from .errors import ExitCode, MWPackError


def main(argv: list[str] | None = None) -> int:
    try:
        return cli.run(argv)
    except MWPackError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return int(exc.exit_code)
    except Exception as exc:  # pragma: no cover
        print(f"internal error: {exc}", file=sys.stderr)
        return int(ExitCode.INTERNAL_ERROR)
