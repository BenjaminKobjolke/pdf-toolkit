"""Draw placed images onto a PDF page using fitz (PyMuPDF).

Companion to :mod:`app.pdf.text_overlay`: the unified ``apply_overlay`` there
calls :func:`draw_image` for each placed image. Kept separate so neither overlay
module approaches the file-length cap. Coordinates map the same way as text — a
scene-pixel rect divided by the render zoom yields PDF points.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from app.pdf.image_assets import resolve_image_path
from app.pdf.image_spec import ImageFieldSpec


def draw_image(page: fitz.Page, image: ImageFieldSpec, zoom: float, base_dir: Path) -> None:
    """Draw ``image`` onto ``page``, resolving its path against ``base_dir``.

    Raises ``ValueError`` if the resolved image file does not exist. PNG alpha is
    honoured (``alpha=-1`` keeps the file's own transparency); the on-page size is
    the stored scene-pixel rect converted to points.
    """
    from app.pdf.text_overlay import scene_to_pdf_rect

    resolved = resolve_image_path(image.path, image.absolute, base_dir)
    if not resolved.is_file():
        raise ValueError(f"image file not found: {resolved}")

    x0, y0, x1, y1 = scene_to_pdf_rect(image.x, image.y, image.width, image.height, zoom)
    page.insert_image(
        fitz.Rect(x0, y0, x1, y1),
        filename=str(resolved),
        keep_proportion=True,
        overlay=True,
    )
