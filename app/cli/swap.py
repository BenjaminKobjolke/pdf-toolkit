"""CLI entry point: swap the two pages of a 2-page PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import EXIT_USAGE, run_with_backup
from app.config.settings import Settings
from app.logging_setup import configure_logging
from app.pdf.swapper import swap_two_pages


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-swap",
        description="Swap the two pages of a 2-page PDF, overwriting the original.",
    )
    parser.add_argument("pdf", type=Path, help="Path to a 2-page PDF.")
    return parser.parse_args(argv)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE
    return run_with_backup(args.pdf, swap_two_pages, settings)


if __name__ == "__main__":
    sys.exit(main())
