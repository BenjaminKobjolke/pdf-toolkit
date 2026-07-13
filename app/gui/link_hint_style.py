"""Shared live holder for the link-overlay appearance settings.

The :class:`LinkHints` overlay and the :class:`LinkHintSettingsController` share
one instance: the controller writes new settings via :meth:`set`, and the overlay
reads them via :meth:`settings` each time it redraws. Mirrors
:mod:`app.gui.outline_style` (minus the drawing, which ``LinkHints`` does inline).
"""

from __future__ import annotations

from app.config.link_hint_settings import LinkHintSettings


class LinkHintStyle:
    """Holds the current link-overlay appearance for the overlay to read."""

    def __init__(self) -> None:
        self._settings = LinkHintSettings()

    def set(self, settings: LinkHintSettings) -> None:
        self._settings = settings

    def settings(self) -> LinkHintSettings:
        return self._settings
