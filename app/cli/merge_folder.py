"""CLI entry point: merge a folder of PDFs and images into a single PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import run_cli, run_folder_merge
from app.pdf.merger import merge_folder


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-merge-folder",
        description=(
            "Merge all PDFs and images (.pdf, .jpg, .jpeg, .png) in a folder into "
            "<folder>/merged.pdf. Existing merged.pdf is backed up first."
        ),
    )
    parser.add_argument("folder", type=Path, help="Folder to scan for files to merge.")
    return parser.parse_args(argv)


def main() -> int:
    return run_cli(_parse_args, lambda a: a.folder, lambda a: merge_folder, runner=run_folder_merge)


if __name__ == "__main__":
    sys.exit(main())
