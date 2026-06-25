"""Shared color conversion for the fitz overlay drawers.

``#rrggbb`` hex (how colors cross every module boundary) -> the 0..1 RGB float
triple PyMuPDF expects. Used by both the text and rectangle overlay drawers.
"""

from __future__ import annotations

_RGB_MAX = 255.0
_HEX_LENGTH = 7  # "#rrggbb"


def hex_to_rgbf(value: str) -> tuple[float, float, float]:
    """Convert ``#rrggbb`` to a ``(r, g, b)`` float triple in 0..1."""
    if len(value) != _HEX_LENGTH or not value.startswith("#"):
        raise ValueError(f"color must be '#rrggbb', got {value!r}")
    try:
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
    except ValueError as err:
        raise ValueError(f"invalid color {value!r}: {err}") from err
    return (r / _RGB_MAX, g / _RGB_MAX, b / _RGB_MAX)
