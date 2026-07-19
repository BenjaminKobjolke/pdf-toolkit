"""The "Remembered settings" command: reset stored preferences.

Lists every :class:`RecordStore` by its ``label`` (self-describing — no hardcoded
table) plus a "clear all" entry, and resets the chosen one (or all).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtWidgets import QWidget

from app.config.record_store import RecordStore
from app.gui import strings
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.operations import OpResult


class RememberedSettingsController:
    """Show the remembered-settings picker and reset what the user chooses."""

    def __init__(
        self,
        parent: QWidget | None,
        stores: Sequence[RecordStore],
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._stores = list(stores)
        self._report = report

    def open(self) -> None:
        """Prompt for a setting to reset (or clear all) and apply it."""
        entries = [ListEntry(title=store.label, payload=store) for store in self._stores]
        entries.append(ListEntry(title=strings.REMEMBERED_CLEAR_ALL, payload=None))
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=strings.REMEMBERED_PLACEHOLDER,
                title=strings.REMEMBERED_TITLE,
            ),
            parent=self._parent,
        )
        if not dialog.exec() or (chosen := dialog.chosen()) is None:
            return
        store = chosen.payload
        if store is None:
            for each in self._stores:
                each.reset()
            self._report(OpResult(True, strings.MSG_REMEMBERED_CLEARED))
        else:
            store.reset()
            self._report(OpResult(True, strings.MSG_REMEMBERED_RESET_FMT.format(name=store.label)))
