"""Input wiring for the main window: the File menu and keyboard shortcuts.

Kept out of :class:`MainWindow` so the window stays a thin coordinator. The
palette has its own chord; every other shortcut resolves through the command
registry so each action is defined exactly once.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtGui import QKeySequence, QShortcut

from app.gui import commands, strings
from app.gui.commands import Command

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow

# Direct keyboard shortcuts -> command id. The palette has its own chord below.
_SHORTCUTS: tuple[tuple[str, str], ...] = (
    ("PgDown", commands.NEXT_PAGE),
    ("PgUp", commands.PREV_PAGE),
    ("Home", commands.FIRST_PAGE),
    ("End", commands.LAST_PAGE),
    ("Ctrl++", commands.ZOOM_IN),
    ("Ctrl+=", commands.ZOOM_IN),
    ("Ctrl+Up", commands.ZOOM_IN),
    ("Ctrl+-", commands.ZOOM_OUT),
    ("Ctrl+Down", commands.ZOOM_OUT),
    ("Ctrl+0", commands.ZOOM_ACTUAL),
    ("Ctrl+F", commands.SEARCH_PDF),
    ("Ctrl+Shift+F", commands.SEARCH_FIELDS),
    ("Ctrl+Shift+H", commands.CLEAR_HIGHLIGHTS),
    ("Ctrl+S", commands.SAVE),
    ("Ctrl+R", commands.ROTATE_RIGHT),
    ("Ctrl+Shift+R", commands.ROTATE_LEFT),
    ("F1", commands.SHOW_SHORTCUTS),
)
_PALETTE_CHORD = "Ctrl+Shift+P"

# Mouse-wheel gestures handled by PageInputController. Not bound to commands, so
# they are listed as static (gesture, description) rows in the controls dialog.
_MOUSE_CONTROLS: tuple[tuple[str, str], ...] = (
    (strings.MOUSE_WHEEL, strings.MOUSE_WHEEL_DESC),
    (strings.MOUSE_SHIFT_WHEEL, strings.MOUSE_SHIFT_WHEEL_DESC),
    (strings.MOUSE_CTRL_WHEEL, strings.MOUSE_CTRL_WHEEL_DESC),
)


def shortcut_pairs(registry: list[Command]) -> list[tuple[str, str]]:
    """Return ``(chord/gesture, title)`` rows for the controls dialog.

    Single source for the controls dialog: keyboard titles are resolved through
    the same registry the shortcuts trigger so they never drift; mouse gestures
    are appended from the static :data:`_MOUSE_CONTROLS` table.
    """
    pairs = [(_PALETTE_CHORD, strings.ACTION_COMMAND_PALETTE)]
    for chord, command_id in _SHORTCUTS:
        pairs.append((chord, commands.find(registry, command_id).title))
    pairs.extend(_MOUSE_CONTROLS)
    return pairs


def build_file_menu(window: MainWindow) -> None:
    """Add the File menu to ``window``'s menu bar."""
    menu = window.menuBar().addMenu(strings.MENU_FILE)
    menu.addAction(strings.ACTION_COMMAND_PALETTE, window.open_command_palette)
    menu.addAction(strings.ACTION_OPEN, lambda: window.open_pdf())
    menu.addAction(strings.ACTION_OPEN_HISTORY, window.open_from_history)
    menu.addSeparator()
    menu.addAction(strings.ACTION_QUIT, window.close)


def install_shortcuts(window: MainWindow, registry: list[Command]) -> None:
    """Register the palette chord and every direct shortcut on ``window``."""
    QShortcut(QKeySequence(_PALETTE_CHORD), window, window.open_command_palette)
    for chord, command_id in _SHORTCUTS:
        command = commands.find(registry, command_id)
        QShortcut(QKeySequence(chord), window, _guarded(command))


def _guarded(command: Command) -> Callable[[], None]:
    """Wrap a command so a shortcut is a no-op when the command is disabled."""

    def trigger() -> None:
        if command.is_enabled():
            command.run()

    return trigger
