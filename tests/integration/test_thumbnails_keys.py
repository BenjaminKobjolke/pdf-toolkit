"""Integration: grid navigation keys beat user-bound single-key shortcuts."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.config.key_bindings import assign, merge_keymap
from app.gui import commands
from app.gui.main_window import MainWindow
from app.gui.window_input import default_shortcut_pairs
from tests.conftest import MakePdf

# The ``window`` fixture comes from tests/conftest.py.


def test_user_bound_right_arrow_navigates_grid_not_shortcut(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    # The user binds "Next file in directory" to a bare arrow; inside the grid
    # the arrow must keep moving the selection, not fire the shortcut.
    first = make_pdf([(100, 100)], name="a.pdf")
    second = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(first)
    overrides = assign(window._key_bindings.load(), "Right", commands.NEXT_FILE)
    window._key_bindings.save(overrides)
    window.apply_keymap(merge_keymap(default_shortcut_pairs(), overrides))
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()

    grid = window._thumbnails_view
    override = QKeyEvent(
        QEvent.Type.ShortcutOverride, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier
    )
    override.ignore()
    QApplication.sendEvent(grid, override)
    # Accepted override = Qt delivers the key to the grid, not the QShortcut.
    assert override.isAccepted()

    grid.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
    )
    assert window.thumbnails_controller.selected_path() == second
    assert window._source == first
