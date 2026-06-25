"""Typed value object describing a filled rectangle placed on a PDF.

Pure data: no Qt, no fitz. Crosses every module boundary (GUI <-> sidecar <->
overlay export), so the fill color is a JSON-friendly hex string. A rectangle is
fill-only (no border); ``width``/``height`` are in render-time scene pixels.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RectFieldSpec:
    """One placed filled rectangle, in render-time scene pixels (top-left origin)."""

    page_index: int  # 0-based
    x: float
    y: float
    width: float
    height: float
    color: str  # "#rrggbb" fill
    z: float = 0.0  # stacking order across all overlay elements (higher = front)
