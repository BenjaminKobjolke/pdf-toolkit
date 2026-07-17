"""Apply :class:`PaletteSettings` to a palette dialog before it is shown.

Kept as a free function (no I/O) so the geometry/flags/opacity logic unit-tests
under the offscreen Qt platform without a running window. Called from
``MainWindow.open_command_palette`` after the dialog is built.
"""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog

from app.config.palette_settings import PaletteSettings
from app.gui.dialog_appearance import apply_chrome, apply_relative_size


def apply_appearance(dialog: QDialog, settings: PaletteSettings, window_size: QSize) -> None:
    """Resize the palette to its width%/height% of the window, then apply the shared chrome.

    Both the resize math and font/opacity/frameless are delegated to
    :mod:`app.gui.dialog_appearance`, the single source every dialog uses.
    """
    apply_relative_size(dialog, settings.width_pct, settings.height_pct, window_size)
    apply_chrome(dialog, settings)
