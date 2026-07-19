"""Draw a placed filled rectangle onto a PDF page using fitz (PyMuPDF).

Mirrors the text/image overlay drawers: the GUI emits the rect in render-time
scene pixels, so the only transform is dividing by the zoom factor
(:func:`scene_to_pdf_rect`). Fill-only, no border.
"""

from __future__ import annotations

import fitz  # PyMuPDF

from app.pdf.colors import hex_to_rgbf
from app.pdf.rect_spec import RectFieldSpec


def draw_rect(page: fitz.Page, rect: RectFieldSpec, zoom: float) -> None:
    """Draw ``rect`` (a filled box) onto ``page``."""
    from app.pdf.text_overlay import scene_to_pdf_rect  # local: shared geometry helper

    x0, y0, x1, y1 = scene_to_pdf_rect(rect, zoom)
    page.draw_rect(
        fitz.Rect(x0, y0, x1, y1),
        fill=hex_to_rgbf(rect.color),
        color=None,
        width=0,
    )
