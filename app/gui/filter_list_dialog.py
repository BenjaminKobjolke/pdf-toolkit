"""A reusable type-to-filter list dialog.

The row model, filtering, and rendering now live in the extracted
``command_palette`` library (``ListEntry``, ``FilterListOptions``,
``ShortcutItemDelegate`` are re-exported unchanged). This subclass only adds
what's app-specific: adopting the shared palette chrome and dialog-size-pct
resizing, same as :class:`~app.gui.filterable_dialog.FilterableListDialog`
(see its docstring for why that's replicated here rather than inherited).
"""

from __future__ import annotations

from typing import TypeVar, cast

from command_palette.dialog import FilterListDialog as _FilterListDialog
from command_palette.dialog import FilterListOptions as FilterListOptions
from command_palette.dialog import ShortcutItemDelegate as ShortcutItemDelegate
from command_palette.entries import ListEntry as ListEntry
from PySide6.QtWidgets import QWidget

from app.gui import dialog_appearance

_DEFAULT_SIZE = (520, 420)

_T = TypeVar("_T")


class FilterListDialog(_FilterListDialog):
    """Filterable single-select list that adopts this app's shared chrome."""

    def exec(self) -> int:
        dialog_appearance.apply_chrome(self, dialog_appearance.active())
        return super().exec()

    def _finish_layout(self, *middle: QWidget) -> None:
        super()._finish_layout(*middle)
        dialog_appearance.resize_for_parent(self, _DEFAULT_SIZE)


def pick_option(
    parent: QWidget | None,
    labels: dict[_T, str],
    *,
    title: str,
    placeholder: str,
) -> _T | None:
    """One-shot option picker: a filterable list of ``labels``, Enter returns the key.

    Shared by every "choose one of a few values" settings command so the
    labels-to-entries-to-dialog dance lives in one place.
    """
    entries = [ListEntry(title=label, payload=key) for key, label in labels.items()]
    dialog = FilterListDialog(
        entries,
        FilterListOptions(placeholder=placeholder, title=title),
        parent=parent,
    )
    if dialog.exec() and (chosen := dialog.chosen()) is not None:
        # payload is typed Any on ListEntry; the labels dict pins its real type.
        return cast("_T", chosen.payload)
    return None
