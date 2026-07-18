"""Persisted, cross-session appearance settings for the command palette.

Tunes the palette window itself — its size (as a percentage of the main window),
font size, frameless chrome, and opacity. Stored as JSON next to the other config
stores, using the same versioned-dict pattern as :mod:`app.config.ui_state`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

PALETTE_SETTINGS_VERSION = 1
PALETTE_KEY = "palette"

# Bounds — single source of truth shared by the edit prompts (MainWindow) and the
# applier clamp (palette_appearance), so the two can never drift apart.
WIDTH_PCT_MIN, WIDTH_PCT_MAX = 20, 100
HEIGHT_PCT_MIN, HEIGHT_PCT_MAX = 20, 100
DIALOG_PCT_MIN, DIALOG_PCT_MAX = 20, 100
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
    # Size of every non-palette list/picker dialog, as % of the window (both axes).
    dialog_size_pct: int = 60


class PaletteSettingsStore(SettingsRecordStore[PaletteSettings]):
    """Reads and writes :class:`PaletteSettings` via the storage backend."""

    LABEL = "Command-palette appearance"
    VERSION = PALETTE_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, PALETTE_KEY, PaletteSettings())
