"""CLI entry point: extract a 1-based page of a PDF into its own new file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli, run_to_new_file
from app.pdf.extractor import default_extract_dest, extract_page


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-extract-page",
        description="Extract a 1-based page into its own file; the original is left untouched.",
    )
    parser.add_argument("page", type=int, help="1-based page number to extract.")
    parser.add_argument("pdf", type=Path, help="Path to the source PDF.")
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="Destination file. Default: <name>-pNN.pdf beside the source.",
    )
    return parser.parse_args(argv)


def _dest(args: argparse.Namespace) -> Path:
    return args.out if args.out is not None else default_extract_dest(args.pdf, args.page)


def main() -> int:
    return run_cli(
        _parse_args,
        lambda a: a.pdf,
        lambda a: lambda p: extract_page(p, a.page, _dest(a)),
        runner=run_to_new_file,
    )


if __name__ == "__main__":
    sys.exit(main())
