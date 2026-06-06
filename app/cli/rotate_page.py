"""CLI entry point: rotate a 1-based page of a PDF clockwise."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli
from app.pdf.rotator import ROTATE_FLIP, ROTATE_LEFT, ROTATE_RIGHT, rotate_page


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-rotate-page",
        description="Rotate a 1-based page of a PDF clockwise, overwriting the original.",
    )
    parser.add_argument("page", type=int, help="1-based page number to rotate.")
    parser.add_argument(
        "degrees",
        type=int,
        choices=[ROTATE_RIGHT, ROTATE_FLIP, ROTATE_LEFT],
        help="Clockwise rotation: 90 (right), 180 (flip), 270 (left).",
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF.")
    return parser.parse_args(argv)


def main() -> int:
    return run_cli(
        _parse_args, lambda a: a.pdf, lambda a: lambda p: rotate_page(p, a.page, a.degrees)
    )


if __name__ == "__main__":
    sys.exit(main())
