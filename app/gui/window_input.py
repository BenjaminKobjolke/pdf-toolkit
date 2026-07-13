"""Input wiring for the main window: the File menu and keyboard shortcuts.

Kept out of :class:`MainWindow` so the window stays a thin coordinator. The
palette has its own chord; every other shortcut resolves through the command
registry so each action is defined exactly once.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from app.gui import commands, overlay_commands, release_strings, strings
from app.gui.commands import Command
from app.gui.shortcut_installer import ShortcutInstaller, TriggerFactory

if TYPE_CHECKING:
    from app.config.key_bindings import DefaultPair, KeyMap
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
    ("Ctrl+Shift+S", commands.SELECT_MODE),
    ("Ctrl+R", commands.ROTATE_RIGHT),
    ("Ctrl+Shift+R", commands.ROTATE_LEFT),
    ("F1", commands.SHOW_SHORTCUTS),
    ("Ctrl+]", overlay_commands.LAYER_FORWARD),
    ("Ctrl+[", overlay_commands.LAYER_BACKWARD),
    ("Ctrl+Shift+]", overlay_commands.LAYER_TO_FRONT),
    ("Ctrl+Shift+[", overlay_commands.LAYER_TO_BACK),
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


def default_shortcut_pairs() -> list[DefaultPair]:
    """The built-in ``(chord, command_id)`` bindings, including the palette chord.

    Single source of the defaults: the static :data:`_SHORTCUTS` table plus the
    palette chord (now a normal, rebindable command). These are passed into
    :func:`app.config.key_bindings.merge_keymap`; the chord literal lives only in
    :data:`_PALETTE_CHORD`.
    """
    return [*_SHORTCUTS, (_PALETTE_CHORD, commands.COMMAND_PALETTE)]


def mouse_control_pairs() -> list[tuple[str, str]]:
    """The ``(gesture, description)`` rows for the read-only mouse-controls list."""
    return list(_MOUSE_CONTROLS)


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
    edit.edit_mode_toggled.connect(window.rects.set_edit_mode)
    edit.edit_mode_toggled.connect(window.mode_bar.set_edit_mode)
    edit.edit_mode_toggled.connect(window.select_controller.on_edit_mode_toggled)
    edit.add_field_requested.connect(window.add_text_field)
    edit.add_image_requested.connect(window.add_image)
    edit.add_rect_requested.connect(window.add_rect)
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
    menu.addAction(release_strings.ACTION_RELEASE_NOTES, window.show_release_notes)
    menu.addSeparator()
    menu.addAction(strings.ACTION_QUIT, window.close)


def install_shortcuts(
    window: MainWindow, registry: list[Command], keymap: KeyMap
) -> ShortcutInstaller:
    """Build a :class:`ShortcutInstaller`, install ``keymap``, and return it.

    Returned so the window can hand it to the shortcut-config flow for live
    reinstalls; the actual ``QShortcut`` creation lives only in the installer.
    """
    installer = ShortcutInstaller(window, registry, _make_trigger_factory(window))
    installer.reinstall(keymap)
    return installer


def _make_trigger_factory(window: MainWindow) -> TriggerFactory:
    """Return a factory mapping a command to its shortcut trigger.

    Preserves the zoom-or-scale behaviour for the zoom commands; every other
    command gets the plain enabled-guard trigger.
    """

    def factory(command: Command) -> Callable[[], None]:
        if command.command_id in _ZOOM_SCALE_FACTORS:
            return _zoom_or_scale(window, command, _ZOOM_SCALE_FACTORS[command.command_id])
        return _guarded(window, command)

    return factory


def _guarded(window: MainWindow, command: Command) -> Callable[[], None]:
    """Wrap a command so a shortcut is a no-op when it's disabled or unavailable
    for the open document's format."""

    def trigger() -> None:
        if command.available(window.current_format()):
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
        elif command.available(window.current_format()):
            command.run()

    return trigger
