"""Write placed text fields onto a PDF using fitz (PyMuPDF).

The GUI emits fields in render-time *scene pixels* (the page is rasterised at
``render.DEFAULT_ZOOM``). Both Qt's scene and a fitz page use a top-left,
y-down origin, so the only transform is dividing by the zoom factor. The source
PDF is overwritten atomically (tmp + ``os.replace``), matching the other ops.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from pathlib import Path

import fitz  # PyMuPDF

from app.pdf.fonts import FontRequest, ResolvedFont, resolve_font
from app.pdf.text_spec import TextFieldSpec

log = logging.getLogger("pdf_toolkit")

_TMP_SUFFIX = ".pdf.tmp"
_RGB_MAX = 255.0
_HEX_LENGTH = 7  # "#rrggbb"
EMBEDDED_SUFFIX = "_text-embedded"


def embedded_output_path(source: Path) -> Path:
    """Return ``source`` with ``_text-embedded`` before the extension."""
    return source.with_name(f"{source.stem}{EMBEDDED_SUFFIX}{source.suffix}")


def scene_to_pdf_rect(
    x_px: float, y_px: float, w_px: float, h_px: float, zoom: float
) -> tuple[float, float, float, float]:
    """Map a scene-pixel rect to a PDF-point rect ``(x0, y0, x1, y1)``."""
    point = 1.0 / zoom
    x0 = x_px * point
    y0 = y_px * point
    return (x0, y0, x0 + w_px * point, y0 + h_px * point)


def screen_px_to_point_size(size_px: float, zoom: float) -> float:
    """Convert a screen-pixel font size to a PDF point size."""
    return size_px / zoom


def apply_text_overlay(
    source: Path, fields: Sequence[TextFieldSpec], output: Path | None = None
) -> None:
    """Draw ``fields`` onto ``source`` and write the result to ``output``.

    ``output`` defaults to ``source`` (overwrite in place). The write is atomic
    (tmp + ``os.replace``). Raises ``ValueError`` if the PDF is encrypted, a
    field targets a missing page, a colour is malformed, or text cannot be
    fitted into its box.
    """
    from app.gui import render  # local import: avoid a Qt dependency at import time

    target = output if output is not None else source
    doc = fitz.open(str(source))
    try:
        if doc.is_encrypted:
            raise ValueError(f"PDF is encrypted: {source}")
        total = int(doc.page_count)
        for field in fields:
            if not 0 <= field.page_index < total:
                raise ValueError(
                    f"page index {field.page_index} out of range; PDF has {total} pages"
                )
            _draw_field(doc.load_page(field.page_index), field, render.DEFAULT_ZOOM)

        tmp = target.with_suffix(_TMP_SUFFIX)
        doc.save(str(tmp), garbage=4, deflate=True)
    finally:
        doc.close()

    os.replace(tmp, target)


def _draw_field(page: fitz.Page, field: TextFieldSpec, zoom: float) -> None:
    x0, y0, x1, y1 = scene_to_pdf_rect(field.x, field.y, field.width, field.height, zoom)
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


def _hex_to_rgbf(value: str) -> tuple[float, float, float]:
    if len(value) != _HEX_LENGTH or not value.startswith("#"):
        raise ValueError(f"colour must be '#rrggbb', got {value!r}")
    try:
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
    except ValueError as err:
        raise ValueError(f"invalid colour {value!r}: {err}") from err
    return (r / _RGB_MAX, g / _RGB_MAX, b / _RGB_MAX)
