"""Persisted, cross-session appearance for text/markdown documents.

Tunes how ``.txt`` and ``.md`` files render in the viewer: the base font size and
a light/dark reading theme. These drive the CSS of the HTML the text renderer
builds (see :mod:`app.pdf.text_html`). Uses the same versioned-dict pattern as
:mod:`app.config.link_hint_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
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


class TextViewSettingsStore(SettingsRecordStore[TextViewSettings]):
    """Reads and writes :class:`TextViewSettings` via the storage backend."""

    LABEL = "Text/Markdown appearance"
    VERSION = TEXT_VIEW_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, TEXT_VIEW_KEY, TextViewSettings())
