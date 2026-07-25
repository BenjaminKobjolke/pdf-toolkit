"""Shared base for the keyboard-first filter dialogs.

The filter-box-over-a-list widget and its Up/Down/Enter/Esc/Del interaction
now live in the extracted ``command_palette`` library. This subclass layers on
the two things every small dialog in this app shares — the live palette
chrome (font size, opacity, frameless flag) and dialog-size-pct resizing —
which :class:`~app.gui.base_dialog.BaseDialog` gives every *other* dialog.
``FilterableListDialog`` can't inherit ``BaseDialog`` too (PySide6 doesn't
support two ``QDialog``-derived bases), so the two calls are replicated here
instead; :mod:`app.gui.dialog_appearance` stays their single source of truth.
"""

from __future__ import annotations

from command_palette.dialog import FilterableListDialog as _FilterableListDialog
from PySide6.QtWidgets import QWidget

from app.gui import dialog_appearance

_DEFAULT_SIZE = (520, 420)


class FilterableListDialog(_FilterableListDialog):
    """Filter box + list (from ``command_palette``) that adopts this app's chrome."""

    def exec(self) -> int:
        dialog_appearance.apply_chrome(self, dialog_appearance.active())
        return super().exec()

    def _finish_layout(self, *middle: QWidget, size: tuple[int, int] = _DEFAULT_SIZE) -> None:
        super()._finish_layout(*middle)
        dialog_appearance.resize_for_parent(self, size)
