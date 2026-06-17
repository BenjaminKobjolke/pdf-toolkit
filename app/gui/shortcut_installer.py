"""Owns the live set of ``QShortcut`` objects so bindings can be rebuilt at runtime.

The original wiring created shortcuts and discarded the references, so nothing
could ever be changed. This manager keeps them: :meth:`reinstall` tears down the
current shortcuts and rebuilds them from an effective :class:`KeyMap`, which is
exactly what both startup and a user reconfigure call — one code path, no second
copy of the build loop.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtGui import QKeySequence, QShortcut

from app.gui import commands
from app.gui.commands import Command

if TYPE_CHECKING:
    from app.config.key_bindings import KeyMap
    from app.gui.main_window import MainWindow

TriggerFactory = Callable[[Command], Callable[[], None]]


class ShortcutInstaller:
    """Creates, retains, and rebuilds the window's keyboard shortcuts."""

    def __init__(
        self, window: MainWindow, registry: list[Command], trigger_factory: TriggerFactory
    ) -> None:
        self._window = window
        self._registry = registry
        self._trigger_factory = trigger_factory
        self._shortcuts: list[QShortcut] = []

    def reinstall(self, keymap: KeyMap) -> None:
        """Discard the current shortcuts and rebuild them from ``keymap``."""
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)
            shortcut.setParent(None)
            shortcut.deleteLater()
        self._shortcuts = []
        for chord, command_id in keymap.bindings:
            try:
                command = commands.find(self._registry, command_id)
            except KeyError:
                continue
            trigger = self._trigger_factory(command)
            self._shortcuts.append(QShortcut(QKeySequence(chord), self._window, trigger))

    def shortcuts(self) -> list[QShortcut]:
        """Return the live shortcuts (used by tests to assert the rebuild)."""
        return list(self._shortcuts)
