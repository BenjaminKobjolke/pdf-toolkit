"""CLI entry point: delete a 1-based page from a PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli
from app.pdf.deleter import delete_page


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-delete-page",
        description="Delete a 1-based page from a PDF, overwriting the original.",
    )
    parser.add_argument("page", type=int, help="1-based page number to delete.")
    parser.add_argument("pdf", type=Path, help="Path to the PDF.")
    return parser.parse_args(argv)


def main() -> int:
    return run_cli(_parse_args, lambda a: a.pdf, lambda a: lambda p: delete_page(p, a.page))


if __name__ == "__main__":
    sys.exit(main())
