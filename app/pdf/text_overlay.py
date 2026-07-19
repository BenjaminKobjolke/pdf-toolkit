"""Write placed text fields onto a PDF using fitz (PyMuPDF).

The GUI emits fields in render-time *scene pixels* (the page is rasterised at
``render.DEFAULT_ZOOM``). Both Qt's scene and a fitz page use a top-left,
y-down origin, so the only transform is dividing by the zoom factor. The source
PDF is overwritten atomically (tmp + ``os.replace``), matching the other ops.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import fitz  # PyMuPDF

from app.io.fs import replace_atomic
from app.pdf._inputs import encrypted_error
from app.pdf.colors import hex_to_rgbf as _hex_to_rgbf
from app.pdf.fonts import FontRequest, ResolvedFont, resolve_font
from app.pdf.image_overlay import draw_image
from app.pdf.image_spec import ImageFieldSpec
from app.pdf.rect_overlay import draw_rect
from app.pdf.rect_spec import RectFieldSpec
from app.pdf.text_spec import TextFieldSpec

_TMP_SUFFIX = ".pdf.tmp"
EMBEDDED_SUFFIX = "_text-embedded"


def embedded_output_path(source: Path) -> Path:
    """Return ``source`` with ``_text-embedded`` before the extension."""
    return source.with_name(f"{source.stem}{EMBEDDED_SUFFIX}{source.suffix}")


class SceneBox(Protocol):
    """Anything with a scene-pixel bounding box (the overlay field specs)."""

    @property
    def x(self) -> float: ...

    @property
    def y(self) -> float: ...

    @property
    def width(self) -> float: ...

    @property
    def height(self) -> float: ...


def scene_to_pdf_rect(box: SceneBox, zoom: float) -> tuple[float, float, float, float]:
    """Map ``box``'s scene-pixel rect to a PDF-point rect ``(x0, y0, x1, y1)``."""
    point = 1.0 / zoom
    x0 = box.x * point
    y0 = box.y * point
    return (x0, y0, x0 + box.width * point, y0 + box.height * point)


def screen_px_to_point_size(size_px: float, zoom: float) -> float:
    """Convert a screen-pixel font size to a PDF point size."""
    return size_px / zoom


def apply_text_overlay(
    source: Path, fields: Sequence[TextFieldSpec], output: Path | None = None
) -> None:
    """Draw text ``fields`` onto ``source`` (thin wrapper over :func:`apply_overlay`).

    Kept as the text-only entry point used by callers and tests that have no
    images; image resolution is irrelevant, so ``base_dir`` defaults to the
    source's directory.
    """
    apply_overlay(source, fields, (), base_dir=source.parent, output=output)


def apply_overlay(
    source: Path,
    fields: Sequence[TextFieldSpec],
    images: Sequence[ImageFieldSpec],
    rects: Sequence[RectFieldSpec] = (),
    *,
    base_dir: Path,
    output: Path | None = None,
) -> None:
    """Draw ``fields``, ``images``, and ``rects`` onto ``source`` in one pass.

    All elements are drawn back-to-front by their ``z`` (stable on ties), so the
    flattened PDF matches the on-screen stacking. ``output`` defaults to
    ``source`` (overwrite in place). Image paths resolve against ``base_dir`` (the
    original PDF's directory). The write is atomic (tmp + ``os.replace``). Raises
    ``ValueError`` if the PDF is encrypted, any element targets a missing page, a
    color is malformed, text cannot be fitted, or an image file is missing.
    """
    from app.gui import render  # local import: avoid a Qt dependency at import time

    zoom = render.DEFAULT_ZOOM
    target = output if output is not None else source
    doc = fitz.open(str(source))
    try:
        if doc.is_encrypted:
            raise encrypted_error(source)
        total = int(doc.page_count)
        for element in _ordered_by_z(fields, images, rects):
            _require_page(element.page_index, total)
            page = doc.load_page(element.page_index)
            if isinstance(element, TextFieldSpec):
                _draw_field(page, element, zoom)
            elif isinstance(element, ImageFieldSpec):
                draw_image(page, element, zoom, base_dir)
            else:
                draw_rect(page, element, zoom)

        tmp = target.with_suffix(_TMP_SUFFIX)
        doc.save(str(tmp), garbage=4, deflate=True)
    finally:
        doc.close()

    replace_atomic(tmp, target)


def _ordered_by_z(
    fields: Sequence[TextFieldSpec],
    images: Sequence[ImageFieldSpec],
    rects: Sequence[RectFieldSpec],
) -> list[TextFieldSpec | ImageFieldSpec | RectFieldSpec]:
    """Merge every element into one back-to-front list, stable on equal ``z``."""
    elements: list[TextFieldSpec | ImageFieldSpec | RectFieldSpec] = [*fields, *images, *rects]
    return sorted(elements, key=lambda element: element.z)


def _require_page(page_index: int, total: int) -> None:
    if not 0 <= page_index < total:
        raise ValueError(f"page index {page_index} out of range; PDF has {total} pages")


def _draw_field(page: fitz.Page, field: TextFieldSpec, zoom: float) -> None:
    x0, y0, x1, y1 = scene_to_pdf_rect(field, zoom)
    size_pt = screen_px_to_point_size(field.font_size, zoom)
    color = _hex_to_rgbf(field.color)
    resolved = resolve_font(FontRequest(field.font_family, field.bold, field.italic))

    if field.bg_color is not None:
        page.draw_rect(
            fitz.Rect(x0, y0, x1, y1),
            fill=_hex_to_rgbf(field.bg_color),
            color=None,
            width=0,
        )

    if not field.text:
        return

    font = _load_font(resolved)
    ascent = font.ascender * size_pt
    line_height = (font.ascender - font.descender) * size_pt
    kwargs = {"fontname": resolved.fontname}
    if resolved.fontfile is not None:
        kwargs["fontfile"] = str(resolved.fontfile)

    # insert_text places each line by its baseline and never wraps, so a field
    # keeps the same line breaks it had on screen instead of reflowing to width.
    for index, line in enumerate(field.text.split("\n")):
        baseline = fitz.Point(x0, y0 + ascent + index * line_height)
        page.insert_text(baseline, line, fontsize=size_pt, color=color, **kwargs)


def _load_font(resolved: ResolvedFont) -> fitz.Font:
    if resolved.fontfile is not None:
        return fitz.Font(fontfile=str(resolved.fontfile))
    return fitz.Font(fontname=resolved.fontname)
