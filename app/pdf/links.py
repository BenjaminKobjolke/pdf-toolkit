"""Per-page hyperlink geometry from a PDF via fitz (PyMuPDF).

Returns typed :class:`LinkBox` values in PDF points (top-left, y-down origin) —
the same coordinate space the GUI converts from when drawing overlays (scene
pixels = points x ``render.DEFAULT_ZOOM``). No fitz objects cross this module's
boundary, matching :mod:`app.pdf.search` and :mod:`app.pdf.words`.

Two sources are merged: real link annotations (``page.get_links`` with a
``uri``) and bare ``http(s)://`` URLs printed in the page text. A text URL whose
uri already appears as an annotation is dropped so a hyperlink shown as its own
URL yields a single hint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from app.pdf.file_format import open_fitz

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_TRAILING = ".,;:!?)]}>\"'"  # punctuation that commonly abuts a printed URL


@dataclass(frozen=True)
class LinkBox:
    """One link: its bounding rect in PDF points and the target URI."""

    x0: float
    y0: float
    x1: float
    y1: float
    uri: str


def page_links(source: Path, page_index: int) -> list[LinkBox]:
    """Return every http(s) link on ``page_index`` of ``source``, in reading order.

    Annotation links come first, then printed URLs not already covered by an
    annotation. A page with no links returns ``[]``.
    """
    doc = open_fitz(source)
    try:
        page = doc.load_page(page_index)
        annotations = _annotation_links(page)
        text_links = _text_links(page)
    finally:
        doc.close()
    annotated = {link.uri for link in annotations}
    return annotations + [link for link in text_links if link.uri not in annotated]


def _annotation_links(page: fitz.Page) -> list[LinkBox]:
    links: list[LinkBox] = []
    for link in page.get_links():
        uri = link.get("uri")
        rect = link.get("from")
        if not uri or rect is None:
            continue
        links.append(
            LinkBox(float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1), str(uri))
        )
    return links


def _text_links(page: fitz.Page) -> list[LinkBox]:
    links: list[LinkBox] = []
    for word in page.get_text("words", sort=True):
        match = _URL_RE.search(str(word[4]))
        if match is None:
            continue
        uri = match.group(0).rstrip(_TRAILING)
        links.append(LinkBox(float(word[0]), float(word[1]), float(word[2]), float(word[3]), uri))
    return links
