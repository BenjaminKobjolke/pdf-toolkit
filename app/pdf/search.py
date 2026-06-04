"""Full-text search over a PDF using fitz (PyMuPDF).

Returns typed :class:`SearchHit` values in PDF points (top-left, y-down origin),
matching the coordinate space the GUI converts from when drawing highlights
(scene pixels = points x ``render.DEFAULT_ZOOM``). No fitz objects cross this
module's boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass(frozen=True)
class SearchHit:
    """One match: its page (0-based), bounding rect in PDF points, and snippet."""

    page_index: int
    x0: float
    y0: float
    x1: float
    y1: float
    snippet: str


def search_pdf(source: Path, query: str) -> list[SearchHit]:
    """Return every match of ``query`` in ``source``, ordered by page.

    Matching is case-insensitive (fitz default). An empty or whitespace-only
    query returns ``[]``.
    """
    if not query.strip():
        return []

    hits: list[SearchHit] = []
    doc = fitz.open(str(source))
    try:
        for page_index in range(int(doc.page_count)):
            page = doc.load_page(page_index)
            for rect in page.search_for(query):
                hits.append(
                    SearchHit(
                        page_index=page_index,
                        x0=float(rect.x0),
                        y0=float(rect.y0),
                        x1=float(rect.x1),
                        y1=float(rect.y1),
                        snippet=_snippet(page, rect),
                    )
                )
    finally:
        doc.close()
    return hits


def _snippet(page: fitz.Page, rect: fitz.Rect) -> str:
    """Best-effort short context for a match, falling back to the matched text."""
    text = page.get_textbox(rect)
    return " ".join(text.split())
