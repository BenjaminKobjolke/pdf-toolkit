"""Typed value objects describing images placed on a PDF, plus the combined
sidecar document.

Pure data: no Qt, no fitz. ``ImageFieldSpec`` crosses every module boundary
(GUI <-> sidecar <-> overlay export). Image paths are stored as plain strings:
relative to the PDF's directory (``assets/<name>``) when copied, or absolute when
the original is merely referenced (see :data:`absolute`).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.pdf.rect_spec import RectFieldSpec
from app.pdf.text_spec import TextFieldSpec


@dataclass(frozen=True)
class ImageFieldSpec:
    """One placed image, in render-time scene pixels (top-left origin).

    ``width``/``height`` are the on-page size in scene pixels (native pixmap size
    times the uniform scale factor). ``path`` is relative to the PDF directory
    when ``absolute`` is false, otherwise an absolute filesystem path.
    """

    page_index: int  # 0-based
    x: float
    y: float
    width: float
    height: float
    path: str  # "assets/<name>" (relative) or an absolute path
    absolute: bool
    opacity: float = 1.0
    z: float = 0.0  # stacking order across all overlay elements (higher = front)


@dataclass(frozen=True)
class SidecarDocument:
    """All overlay content for one PDF: text fields, images, and rects, by page."""

    fields: tuple[TextFieldSpec, ...] = ()
    images: tuple[ImageFieldSpec, ...] = ()
    rects: tuple[RectFieldSpec, ...] = ()

    def fields_on_page(self, page_index: int) -> tuple[TextFieldSpec, ...]:
        """Return the text fields placed on ``page_index`` (0-based)."""
        return tuple(field for field in self.fields if field.page_index == page_index)

    def images_on_page(self, page_index: int) -> tuple[ImageFieldSpec, ...]:
        """Return the images placed on ``page_index`` (0-based)."""
        return tuple(image for image in self.images if image.page_index == page_index)

    def rects_on_page(self, page_index: int) -> tuple[RectFieldSpec, ...]:
        """Return the rectangles placed on ``page_index`` (0-based)."""
        return tuple(rect for rect in self.rects if rect.page_index == page_index)

    def is_empty(self) -> bool:
        """Return whether there is no overlay content at all."""
        return not self.fields and not self.images and not self.rects
