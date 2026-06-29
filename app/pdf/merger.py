"""Merge a folder of PDFs and images into a single ``merged.pdf``."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.logging_setup import log
from app.pdf._atomic import write_pdf_atomic
from app.pdf._inputs import SUPPORTED_EXTENSIONS, pages_for_input

MERGED_FILENAME: str = "merged.pdf"
TMP_SUFFIX: str = ".tmp"


def scan_folder(folder: Path) -> list[Path]:
    """Return supported files in ``folder`` (flat, alphabetical, case-insensitive)."""
    matches: list[Path] = []
    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if entry.name.lower() == MERGED_FILENAME.lower():
            continue
        matches.append(entry)
    return sorted(matches, key=lambda p: p.name.lower())


def find_existing_merged(folder: Path) -> Path | None:
    """Return the existing ``merged.pdf`` in ``folder`` (case-insensitive), or ``None``."""
    for entry in folder.iterdir():
        if entry.is_file() and entry.name.lower() == MERGED_FILENAME.lower():
            return entry
    return None


def merge_folder(folder: Path) -> None:
    """Merge supported files in ``folder`` into ``<folder>/merged.pdf`` atomically.

    Raises ``ValueError`` if the folder is missing, empty of supported files, or
    contains an encrypted PDF.
    """
    if not folder.is_dir():
        raise ValueError(f"folder not found: {folder}")

    inputs = scan_folder(folder)
    if not inputs:
        raise ValueError(f"no supported files in {folder}")

    target = folder / MERGED_FILENAME
    tmp = folder / (MERGED_FILENAME + TMP_SUFFIX)

    writer = PdfWriter()
    try:
        for path in inputs:
            for page in pages_for_input(path):
                writer.add_page(page)

        write_pdf_atomic(target, writer)
        log.info("merged %d files into %s", len(inputs), target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                log.warning("could not remove tmp file: %s", tmp)
