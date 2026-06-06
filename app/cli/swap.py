"""CLI entry point: swap the two pages of a 2-page PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli
from app.pdf.swapper import swap_two_pages


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-swap",
        description="Swap the two pages of a 2-page PDF, overwriting the original.",
    )
    parser.add_argument("pdf", type=Path, help="Path to a 2-page PDF.")
    return parser.parse_args(argv)


def main() -> int:
    return run_cli(_parse_args, lambda a: a.pdf, lambda a: swap_two_pages)


if __name__ == "__main__":
    sys.exit(main())
