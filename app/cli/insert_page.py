"""CLI entry point: insert a PDF or image after a 1-based page of a PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli
from app.pdf.inserter import insert_after


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-insert-page",
        description="Insert a PDF or image after a 1-based page (0 = front), overwriting the PDF.",
    )
    parser.add_argument("insert", type=Path, help="PDF or image file to insert.")
    parser.add_argument("after_page", type=int, help="Insert after this 1-based page (0 = front).")
    parser.add_argument("pdf", type=Path, help="Path to the PDF to insert into.")
    return parser.parse_args(argv)


def main() -> int:
    return run_cli(
        _parse_args,
        lambda a: a.pdf,
        lambda a: lambda p: insert_after(p, a.insert, a.after_page),
    )


if __name__ == "__main__":
    sys.exit(main())
