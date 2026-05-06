"""CLI entry point: merge a folder of PDFs and images into a single PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import EXIT_USAGE, run_folder_merge
from app.config.settings import Settings
from app.logging_setup import configure_logging
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
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE
    return run_folder_merge(args.folder, merge_folder, settings)


if __name__ == "__main__":
    sys.exit(main())
