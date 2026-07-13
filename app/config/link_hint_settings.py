"""Persisted, cross-session appearance for the open/copy-link hint overlay.

Tunes the hints drawn over each link in link mode: the letter font size, the
letter text color, the chip background behind the letter, and the box outline
color around the link. Uses the same versioned-dict pattern as
:mod:`app.config.outline_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
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


class LinkHintSettingsStore(RecordStore):
    """Reads and writes :class:`LinkHintSettings` via the storage backend."""

    LABEL = "Link overlay appearance"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, LINK_HINT_KEY)

    def load(self) -> LinkHintSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, LINK_HINT_SETTINGS_VERSION)
        if raw is None:
            return LinkHintSettings()
        default = LinkHintSettings()
        return LinkHintSettings(
            font_pt=int(raw.get("font_pt", default.font_pt)),
            text_color=str(raw.get("text_color", default.text_color)),
            background_color=str(raw.get("background_color", default.background_color)),
            box_color=str(raw.get("box_color", default.box_color)),
        )

    def save(self, settings: LinkHintSettings) -> None:
        self._backend.set_versioned(
            self._key,
            LINK_HINT_SETTINGS_VERSION,
            {
                "font_pt": settings.font_pt,
                "text_color": settings.text_color,
                "background_color": settings.background_color,
                "box_color": settings.box_color,
            },
        )
