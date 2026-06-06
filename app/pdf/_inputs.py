"""Turn a path (PDF or image) into PDF pages — shared by merge and insert.

Centralizes the two snippets that several core ops would otherwise duplicate:
opening a reader while rejecting encrypted PDFs, and converting a supported input
file (PDF or JPG/PNG image) into a list of pages ready to add to a writer.
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import img2pdf  # type: ignore[import-untyped]
from PIL import Image
from pypdf import PageObject, PdfReader

PDF_EXTENSION: str = ".pdf"
IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png")
SUPPORTED_EXTENSIONS: tuple[str, ...] = (PDF_EXTENSION,) + IMAGE_EXTENSIONS
JPEG_FALLBACK_QUALITY: int = 95

log = logging.getLogger("pdf_toolkit")


def open_reader(source: Path) -> PdfReader:
    """Return a :class:`PdfReader` for ``source``, raising on an encrypted PDF."""
    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {source}")
    return reader


def image_to_pdf_bytes(path: Path) -> bytes:
    """Convert a JPG/PNG at ``path`` into single-page PDF bytes.

    Falls back to an RGB JPEG re-encode when the image has an alpha channel that
    ``img2pdf`` refuses.
    """
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


def pages_for_input(path: Path) -> list[PageObject]:
    """Return the pages contributed by ``path`` (a PDF or an image).

    Raises ``ValueError`` for an encrypted PDF or an unsupported file type.
    """
    suffix = path.suffix.lower()
    if suffix == PDF_EXTENSION:
        return list(open_reader(path).pages)
    if suffix in IMAGE_EXTENSIONS:
        reader = PdfReader(BytesIO(image_to_pdf_bytes(path)))
        return list(reader.pages)
    raise ValueError(f"unsupported file type: {path}")
