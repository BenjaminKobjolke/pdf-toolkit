"""Owns the single-instance preference: load, toggle, persist.

Persists via :class:`InstanceSettingsStore`. The *launching* process reads the
stored value (see :mod:`app.gui.main`), so toggling here needs no restart of
the running viewer. Mirrors :class:`OpenFilterController` so the window stays
a thin coordinator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from app.config.instance_settings import InstanceSettingsStore
from app.gui import settings_strings
from app.gui.operations import OpResult


class InstanceController:
    """Loads, toggles, and persists the single-instance preferences."""

    def __init__(self, store: InstanceSettingsStore, report: Callable[[OpResult], None]) -> None:
        self._store = store
        self._report = report
        self._settings = store.load()

    @property
    def focus_on_forward(self) -> bool:
        """Whether a forwarded open should bring this window to the front."""
        return self._settings.focus_on_forward

    def toggle_reuse_window(self) -> None:
        """Flip the preference and confirm the new state.

        The confirmation matters: unlike most toggles this one changes nothing
        visible in the current window, only future launches.
        """
        self._toggle(
            "reuse_window",
            settings_strings.MSG_REUSE_WINDOW_ON,
            settings_strings.MSG_REUSE_WINDOW_OFF,
        )

    def toggle_focus_on_forward(self) -> None:
        """Flip whether forwarded opens steal focus; confirm the new state."""
        self._toggle(
            "focus_on_forward",
            settings_strings.MSG_FOCUS_ON_FORWARD_ON,
            settings_strings.MSG_FOCUS_ON_FORWARD_OFF,
        )

    def _toggle(self, field: str, msg_on: str, msg_off: str) -> None:
        new_value = not getattr(self._settings, field)
        self._settings = replace(self._settings, **{field: new_value})
        self._store.save(self._settings)
        self._report(OpResult(True, msg_on if new_value else msg_off))
