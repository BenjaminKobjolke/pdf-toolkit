"""Persisted, cross-session appearance for text/markdown documents.

Tunes how ``.txt`` and ``.md`` files render in the viewer: the base font size and
a light/dark reading theme. These drive the CSS of the HTML the text renderer
builds (see :mod:`app.pdf.text_html`). Uses the same versioned-dict pattern as
:mod:`app.config.link_hint_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

TEXT_VIEW_SETTINGS_VERSION = 1
TEXT_VIEW_KEY = "text_view"

# Font-size bounds — single source of truth shared by the edit prompt and clamp.
FONT_PT_MIN, FONT_PT_MAX = 6, 40


@dataclass(frozen=True)
class TextViewSettings:
    """Remembered text/markdown appearance preferences (defaults = built-ins)."""

    font_pt: int = 12
    dark_mode: bool = False


class TextViewSettingsStore(RecordStore):
    """Reads and writes :class:`TextViewSettings` via the storage backend."""

    LABEL = "Text/Markdown appearance"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, TEXT_VIEW_KEY)

    def load(self) -> TextViewSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, TEXT_VIEW_SETTINGS_VERSION)
        if raw is None:
            return TextViewSettings()
        default = TextViewSettings()
        return TextViewSettings(
            font_pt=int(raw.get("font_pt", default.font_pt)),
            dark_mode=bool(raw.get("dark_mode", default.dark_mode)),
        )

    def save(self, settings: TextViewSettings) -> None:
        self._backend.set_versioned(
            self._key,
            TEXT_VIEW_SETTINGS_VERSION,
            {"font_pt": settings.font_pt, "dark_mode": settings.dark_mode},
        )
