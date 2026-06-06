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

# Zoom chords double as image-scale chords: when an image is selected they resize
# it (aspect locked) instead of zooming the page. Maps a zoom command id to its
# scale factor.
_IMAGE_SCALE_STEP = 1.1
_ZOOM_SCALE_FACTORS: dict[str, float] = {
    commands.ZOOM_IN: _IMAGE_SCALE_STEP,
    commands.ZOOM_OUT: 1.0 / _IMAGE_SCALE_STEP,
}

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


def install_control_signals(window: MainWindow) -> None:
    """Connect the operation bar, edit bar, and page-view signals to ``window``.

    Kept here so :class:`MainWindow.__init__` stays a thin sequence of
    constructions; every connection routes to a public window method/controller.
    """
    bar = window.operation_bar
    bar.prev_requested.connect(window.page_view.show_prev)
    bar.next_requested.connect(window.page_view.show_next)
    bar.swap_requested.connect(window.page_actions.swap)
    bar.delete_page_requested.connect(window.page_actions.delete_current_page)
    bar.delete_range_requested.connect(window.page_actions.delete_page_range)
    bar.insert_page_requested.connect(window.page_actions.insert_pages)
    bar.extract_page_requested.connect(window.page_actions.extract_current_page)
    bar.merge_folder_requested.connect(window.page_actions.merge_folder)

    edit = window.edit_bar
    edit.edit_mode_toggled.connect(window.controller.set_edit_mode)
    edit.edit_mode_toggled.connect(window.images.set_edit_mode)
    edit.edit_mode_toggled.connect(window.mode_bar.set_edit_mode)
    edit.add_field_requested.connect(window.add_text_field)
    edit.add_image_requested.connect(window.add_image)
    edit.delete_field_requested.connect(window.controller.delete_selected)
    edit.style_changed.connect(window.controller.apply_style)
    edit.export_text_requested.connect(window.export_text)

    view = window.page_view
    view.page_changed.connect(bar.set_page_label)
    view.page_changed.connect(window.mode_bar.set_page_label)
    view.zoom_changed.connect(window.mode_bar.set_zoom_label)
    view.edit_text_requested.connect(window.field_actions.change_text)


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
        if command_id in _ZOOM_SCALE_FACTORS:
            trigger = _zoom_or_scale(window, command, _ZOOM_SCALE_FACTORS[command_id])
        else:
            trigger = _guarded(command)
        QShortcut(QKeySequence(chord), window, trigger)


def _guarded(command: Command) -> Callable[[], None]:
    """Wrap a command so a shortcut is a no-op when the command is disabled."""

    def trigger() -> None:
        if command.is_enabled():
            command.run()

    return trigger


def _zoom_or_scale(window: MainWindow, command: Command, factor: float) -> Callable[[], None]:
    """Resize the selected overlay element if any; otherwise run the zoom command.

    Lets the zoom keys (``Ctrl+↑/↓``, ``Ctrl++/-``) change a selected text field's
    font size or a selected image's scale, while leaving the palette's explicit
    "Zoom" entries to always zoom the page.
    """

    def trigger() -> None:
        scale = window.images.selected_scale()
        if window.page_view.selected_text_item() is not None:
            window.field_actions.scale_font(factor)
        elif scale is not None:
            window.images.set_selected_scale(scale * factor)
        elif command.is_enabled():
            command.run()

    return trigger
