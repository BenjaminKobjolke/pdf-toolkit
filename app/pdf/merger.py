"""Merge a folder of PDFs and images into a single ``merged.pdf``."""

from __future__ import annotations

import logging
import os
from io import BytesIO
from pathlib import Path

import img2pdf  # type: ignore[import-untyped]
from PIL import Image
from pypdf import PdfReader, PdfWriter

MERGED_FILENAME: str = "merged.pdf"
PDF_EXTENSION: str = ".pdf"
IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png")
SUPPORTED_EXTENSIONS: tuple[str, ...] = (PDF_EXTENSION,) + IMAGE_EXTENSIONS
TMP_SUFFIX: str = ".tmp"
JPEG_FALLBACK_QUALITY: int = 95

log = logging.getLogger("pdf_toolkit")


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
            suffix = path.suffix.lower()
            if suffix == PDF_EXTENSION:
                _append_pdf(writer, path)
            else:
                _append_image(writer, path)

        with tmp.open("wb") as fh:
            writer.write(fh)
        os.replace(tmp, target)
        log.info("merged %d files into %s", len(inputs), target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                log.warning("could not remove tmp file: %s", tmp)


def _append_pdf(writer: PdfWriter, path: Path) -> None:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {path}")
    for page in reader.pages:
        writer.add_page(page)


def _append_image(writer: PdfWriter, path: Path) -> None:
    pdf_bytes = _image_to_pdf_bytes(path)
    reader = PdfReader(BytesIO(pdf_bytes))
    for page in reader.pages:
        writer.add_page(page)


def _image_to_pdf_bytes(path: Path) -> bytes:
    try:
        result: bytes = img2pdf.convert([str(path)])
        return result
    except img2pdf.AlphaChannelError:
        log.info("alpha channel detected, converting to RGB JPEG: %s", path)
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            buffer = BytesIO()
            rgb.save(buffer, format="JPEG", quality=JPEG_FALLBACK_QUALITY)
        fallback: bytes = img2pdf.convert(buffer.getvalue())
        return fallback
