"""Coordinates the deferred working-copy save flow for the viewer window.

Holds the save / confirm-on-exit / dirty-marker logic, extracted from
``MainWindow`` so the window stays a thin coordinator (and under the 300-line
cap). It drives a :class:`WorkingDocument` it does not own — the window keeps
ownership so it can render and mutate the working copy.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from app.gui import confirm_dialog, strings
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.operations import OpResult
from app.gui.working_document import WorkingDocument


class SaveController:
    """Save changes, confirm unsaved-on-exit, and keep the dirty marker in sync."""

    def __init__(
        self,
        parent: QWidget,
        working_doc: WorkingDocument,
        mode_bar: ModeStatusBar,
        report: Callable[[OpResult], None],
        flush: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._doc = working_doc
        self._mode_bar = mode_bar
        self._report = report
        self._flush = flush

    def mark_dirty(self) -> None:
        """Flag the working copy as modified and show the status-bar marker."""
        self._doc.mark_dirty()
        self._mode_bar.set_dirty(True)

    def save(self) -> None:
        """The 'Save changes to original file' command."""
        if not self._doc.is_dirty():
            self._report(OpResult(True, strings.MSG_NO_CHANGES))
            return
        self._flush()
        result = self._doc.save()
        if result.ok:
            self._mode_bar.set_dirty(False)
        self._report(result)

    def confirm_unsaved(self) -> bool:
        """Prompt to save pending changes. Return False to abort the caller."""
        if not self._doc.is_dirty():
            return True
        choice = confirm_dialog.confirm(
            self._parent,
            strings.CONFIRM_UNSAVED_TITLE,
            strings.CONFIRM_UNSAVED_TEXT,
            primary=strings.BTN_SAVE,
            secondary=strings.BTN_DISCARD,
            cancel=strings.BTN_CANCEL,
        )
        if choice is confirm_dialog.DialogResult.CANCEL:
            return False
        if choice is confirm_dialog.DialogResult.PRIMARY:
            self._flush()
            result = self._doc.save()
            if not result.ok:
                self._report(result)
                return False
        else:  # Discard: abandon the working edits
            self._doc.discard()
        self._mode_bar.set_dirty(False)
        return True
