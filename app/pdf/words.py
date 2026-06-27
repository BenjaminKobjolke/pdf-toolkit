"""Per-page word geometry from a PDF via fitz (PyMuPDF).

Returns typed :class:`WordBox` values in PDF points (top-left, y-down origin) and
in reading order — the same coordinate space the GUI converts from when drawing
highlights (scene pixels = points x ``render.DEFAULT_ZOOM``). No fitz objects
cross this module's boundary, matching :mod:`app.pdf.search`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass(frozen=True)
class WordBox:
    """One word: its reading-order index, bounding rect (points), and line origin."""

    index: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block: int
    line: int

    @property
    def line_key(self) -> tuple[int, int]:
        """Identifies the text line this word belongs to (for line motions)."""
        return (self.block, self.line)


def page_words(source: Path, page_index: int) -> list[WordBox]:
    """Return every word on ``page_index`` of ``source``, in reading order.

    Uses fitz ``get_text("words", sort=True)`` so words come pre-ordered top-to-
    bottom, left-to-right. A page with no text returns ``[]``.
    """
    doc = fitz.open(str(source))
    try:
        raw = doc.load_page(page_index).get_text("words", sort=True)
    finally:
        doc.close()
    return [
        WordBox(
            index=i,
            x0=float(w[0]),
            y0=float(w[1]),
            x1=float(w[2]),
            y1=float(w[3]),
            text=str(w[4]),
            block=int(w[5]),
            line=int(w[6]),
        )
        for i, w in enumerate(raw)
    ]


def page_text(source: Path, page_index: int) -> str:
    """Return the full text of ``page_index`` with native line breaks (or "")."""
    doc = fitz.open(str(source))
    try:
        return str(doc.load_page(page_index).get_text("text")).rstrip()
    finally:
        doc.close()
