"""Persisted, cross-session appearance for the open/copy-link hint overlay.

Tunes the hints drawn over each link in link mode: the letter font size, the
letter text color, the chip background behind the letter, and the box outline
color around the link. Uses the same versioned-dict pattern as
:mod:`app.config.outline_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

LINK_HINT_SETTINGS_VERSION = 1
LINK_HINT_KEY = "link_hint"

# Font-size bounds — single source of truth shared by the edit prompt and any
# clamp, so the two can never drift apart.
FONT_PT_MIN, FONT_PT_MAX = 6, 40


@dataclass(frozen=True)
class LinkHintSettings:
    """Remembered link-overlay appearance preferences (defaults = built-ins)."""

    font_pt: int = 9
    text_color: str = "#000000"  # "#rrggbb" — letter color
    background_color: str = "#ffd000"  # chip fill behind the letter
    box_color: str = "#00a000"  # outline around the link


class LinkHintSettingsStore(SettingsRecordStore[LinkHintSettings]):
    """Reads and writes :class:`LinkHintSettings` via the storage backend."""

    LABEL = "Link overlay appearance"
    VERSION = LINK_HINT_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, LINK_HINT_KEY, LinkHintSettings())
