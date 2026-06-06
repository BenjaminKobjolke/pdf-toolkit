"""Persisted, cross-session appearance settings for the command palette.

Tunes the palette window itself — its size (as a percentage of the main window),
font size, frameless chrome, and opacity. Stored as JSON next to the other config
stores, using the same versioned-dict pattern as :mod:`app.config.ui_state`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.io.json_store import read_versioned_dict, write_versioned

PALETTE_SETTINGS_VERSION = 1

# Bounds — single source of truth shared by the edit prompts (MainWindow) and the
# applier clamp (palette_appearance), so the two can never drift apart.
WIDTH_PCT_MIN, WIDTH_PCT_MAX = 20, 100
HEIGHT_PCT_MIN, HEIGHT_PCT_MAX = 20, 100
OPACITY_PCT_MIN, OPACITY_PCT_MAX = 20, 100
FONT_PT_MIN, FONT_PT_MAX = 0, 40  # 0 = inherit the default font size


@dataclass(frozen=True)
class PaletteSettings:
    """Remembered command-palette appearance preferences."""

    width_pct: int = 80
    height_pct: int = 60
    font_pt: int = 0
    borderless: bool = False
    opacity_pct: int = 100


class PaletteSettingsStore:
    """Reads and writes :class:`PaletteSettings` at a fixed JSON path."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> PaletteSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = read_versioned_dict(self._path, PALETTE_SETTINGS_VERSION)
        if raw is None:
            return PaletteSettings()
        default = PaletteSettings()
        return PaletteSettings(
            width_pct=int(raw.get("width_pct", default.width_pct)),
            height_pct=int(raw.get("height_pct", default.height_pct)),
            font_pt=int(raw.get("font_pt", default.font_pt)),
            borderless=bool(raw.get("borderless", default.borderless)),
            opacity_pct=int(raw.get("opacity_pct", default.opacity_pct)),
        )

    def save(self, settings: PaletteSettings) -> None:
        write_versioned(
            self._path,
            PALETTE_SETTINGS_VERSION,
            {
                "width_pct": settings.width_pct,
                "height_pct": settings.height_pct,
                "font_pt": settings.font_pt,
                "borderless": settings.borderless,
                "opacity_pct": settings.opacity_pct,
            },
        )
