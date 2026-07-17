"""Merge a folder of files into a single ``merged.*`` output.

Two kinds of folder are supported, chosen by the files present:
- PDFs and images → a merged ``merged.pdf`` (pages concatenated via ``pypdf``).
- text files (``.txt`` / ``.md``) → a concatenated ``merged.txt`` / ``merged.md``.

A folder mixing the two is rejected. :func:`merged_output_path` is the single
place that classifies a folder and names its output; every caller uses it so the
"which format" decision lives in exactly one spot.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.logging_setup import log
from app.pdf._atomic import write_pdf_atomic, write_text_atomic
from app.pdf._inputs import SUPPORTED_EXTENSIONS, pages_for_input

MERGED_STEM: str = "merged"
MERGED_FILENAME: str = f"{MERGED_STEM}.pdf"
TMP_SUFFIX: str = ".tmp"
TEXT_MERGE_EXTENSIONS: tuple[str, ...] = (".txt", ".md")
TEXT_SEPARATOR: str = "\n\n"

__all__ = [
    "MERGED_FILENAME",
    "MERGED_STEM",
    "TEXT_MERGE_EXTENSIONS",
    "TMP_SUFFIX",
    "find_existing_merged",
    "log",
    "merge_folder",
    "merged_output_path",
    "scan_folder",
]


def scan_folder(folder: Path, extensions: tuple[str, ...] = SUPPORTED_EXTENSIONS) -> list[Path]:
    """Return files in ``folder`` with one of ``extensions`` (flat, alphabetical).

    Case-insensitive on both extension and sort. Any previously produced
    ``merged.*`` output is excluded so re-merging never folds it back in.
    """
    matches: list[Path] = []
    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in extensions:
            continue
        if entry.stem.lower() == MERGED_STEM:
            continue
        matches.append(entry)
    return sorted(matches, key=lambda p: p.name.lower())


def merged_output_path(folder: Path) -> Path:
    """Return the output path for merging ``folder``, classifying it by content.

    ``merged.pdf`` for a pdf/image folder; ``merged.<ext>`` for a text folder
    (the shared text extension when uniform, else ``.txt``). Raises ``ValueError``
    if the folder mixes text with pdf/image files.
    """
    text_files = scan_folder(folder, TEXT_MERGE_EXTENSIONS)
    doc_files = scan_folder(folder, SUPPORTED_EXTENSIONS)
    if text_files and doc_files:
        raise ValueError("cannot merge text and PDF/image files together")
    if text_files:
        suffixes = {p.suffix.lower() for p in text_files}
        ext = suffixes.pop() if len(suffixes) == 1 else ".txt"
        return folder / f"{MERGED_STEM}{ext}"
    return folder / MERGED_FILENAME


def find_existing_merged(folder: Path) -> Path | None:
    """Return an existing ``merged.{pdf,txt,md}`` in ``folder``, or ``None``."""
    outputs = (MERGED_FILENAME, *(f"{MERGED_STEM}{ext}" for ext in TEXT_MERGE_EXTENSIONS))
    lowered = {name.lower() for name in outputs}
    for entry in folder.iterdir():
        if entry.is_file() and entry.name.lower() in lowered:
            return entry
    return None


def merge_folder(folder: Path) -> None:
    """Merge the supported files in ``folder`` into its ``merged.*`` output atomically.

    Raises ``ValueError`` if the folder is missing, empty of supported files, mixes
    text with pdf/image files, or contains an encrypted PDF.
    """
    if not folder.is_dir():
        raise ValueError(f"folder not found: {folder}")

    target = merged_output_path(folder)
    tmp = target.with_suffix(target.suffix + TMP_SUFFIX)
    try:
        if target.suffix.lower() in TEXT_MERGE_EXTENSIONS:
            _merge_text(folder, target)
        else:
            _merge_pdf(folder, target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                log.warning("could not remove tmp file: %s", tmp)


def _merge_pdf(folder: Path, target: Path) -> None:
    inputs = scan_folder(folder)
    if not inputs:
        raise ValueError(f"no supported files in {folder}")
    writer = PdfWriter()
    for path in inputs:
        for page in pages_for_input(path):
            writer.add_page(page)
    write_pdf_atomic(target, writer)
    log.info("merged %d files into %s", len(inputs), target)


def _merge_text(folder: Path, target: Path) -> None:
    inputs = scan_folder(folder, TEXT_MERGE_EXTENSIONS)
    if not inputs:
        raise ValueError(f"no supported files in {folder}")
    merged = TEXT_SEPARATOR.join(path.read_text(encoding="utf-8") for path in inputs)
    write_text_atomic(target, merged)
    log.info("merged %d files into %s", len(inputs), target)
