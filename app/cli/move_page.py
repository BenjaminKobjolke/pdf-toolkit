"""CLI entry point: move a 1-based page to a new position within a PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli
from app.pdf.mover import move_page


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-move-page",
        description="Move a 1-based page to a new 1-based position, overwriting the original.",
    )
    parser.add_argument("from_page", type=int, help="1-based page number to move.")
    parser.add_argument("to_page", type=int, help="1-based destination position.")
    parser.add_argument("pdf", type=Path, help="Path to the PDF.")
    return parser.parse_args(argv)


def main() -> int:
    return run_cli(
        _parse_args, lambda a: a.pdf, lambda a: lambda p: move_page(p, a.from_page, a.to_page)
    )


if __name__ == "__main__":
    sys.exit(main())
