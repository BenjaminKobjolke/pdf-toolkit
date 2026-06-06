"""CLI entry point: delete a 1-based page range from a PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli
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
    return run_cli(
        _parse_args, lambda a: a.pdf, lambda a: lambda p: delete_page_range(p, a.start, a.end)
    )


if __name__ == "__main__":
    sys.exit(main())
