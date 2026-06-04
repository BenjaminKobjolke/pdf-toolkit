"""Typed value objects describing text fields placed on a PDF.

Pure data: no Qt, no fitz. These cross every module boundary (GUI <-> sidecar
<-> overlay export) so colours are JSON-friendly hex strings, not Qt types.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextFieldSpec:
    """One placed text field, in render-time scene pixels (top-left origin)."""

    page_index: int  # 0-based
    x: float
    y: float
    width: float
    height: float
    text: str
    font_family: str
    font_size: float  # scene px (zoom-space)
    color: str  # "#rrggbb"
    bg_color: str | None  # "#rrggbb" or None (transparent)
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class TextDocumentSpec:
    """All text fields for one PDF, across every page."""

    fields: tuple[TextFieldSpec, ...]

    def fields_on_page(self, page_index: int) -> tuple[TextFieldSpec, ...]:
        """Return the fields placed on ``page_index`` (0-based)."""
        return tuple(field for field in self.fields if field.page_index == page_index)
