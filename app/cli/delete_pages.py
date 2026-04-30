"""CLI entry point: delete a 1-based page range from a PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import EXIT_USAGE, run_with_backup
from app.config.settings import Settings
from app.logging_setup import configure_logging
from app.pdf.deleter import delete_page_range


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-delete-pages",
        description=("Delete a 1-based inclusive page range from a PDF, overwriting the original."),
    )
    parser.add_argument("start", type=int, help="1-based start page (inclusive).")
    parser.add_argument("end", type=int, help="1-based end page (inclusive).")
    parser.add_argument("pdf", type=Path, help="Path to the PDF.")
    return parser.parse_args(argv)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE

    def _op(path: Path) -> None:
        delete_page_range(path, args.start, args.end)

    return run_with_backup(args.pdf, _op, settings)


if __name__ == "__main__":
    sys.exit(main())
