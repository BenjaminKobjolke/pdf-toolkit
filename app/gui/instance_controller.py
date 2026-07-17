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
    """Loads, toggles, and persists whether launches reuse the running window."""

    def __init__(self, store: InstanceSettingsStore, report: Callable[[OpResult], None]) -> None:
        self._store = store
        self._report = report
        self._settings = store.load()

    def toggle_reuse_window(self) -> None:
        """Flip the preference and confirm the new state.

        The confirmation matters: unlike the other toggles this one changes
        nothing visible in the current window, only future launches.
        """
        self._settings = replace(self._settings, reuse_window=not self._settings.reuse_window)
        self._store.save(self._settings)
        message = (
            settings_strings.MSG_REUSE_WINDOW_ON
            if self._settings.reuse_window
            else settings_strings.MSG_REUSE_WINDOW_OFF
        )
        self._report(OpResult(True, message))
