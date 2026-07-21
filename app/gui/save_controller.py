"""Coordinates the deferred working-copy save flow for the viewer window.

Holds the save / confirm-on-exit / dirty-marker logic, extracted from
``MainWindow`` so the window stays a thin coordinator (and under the 300-line
cap). It drives a :class:`WorkingDocument` it does not own — the window keeps
ownership so it can render and mutate the working copy.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.gui import confirm_dialog, file_strings, strings
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.operations import OpResult
from app.gui.working_document import WorkingDocument, save_copy


class SaveController:
    """Save changes, confirm unsaved-on-exit, and keep the dirty marker in sync."""

    def __init__(
        self,
        parent: QWidget,
        working_doc: WorkingDocument,
        mode_bar: ModeStatusBar,
        report: Callable[[OpResult], None],
        flush: Callable[[], None],
        on_saved: Callable[[], None] = lambda: None,
    ) -> None:
        self._parent = parent
        self._doc = working_doc
        self._mode_bar = mode_bar
        self._report = report
        self._flush = flush
        self._on_saved = on_saved

    def mark_dirty(self) -> None:
        """Flag the working copy as modified and show the status-bar marker.

        The marker mirrors the document: preview-only formats (PSD) refuse the
        dirty flag, so no Modified marker appears for them either.
        """
        self._doc.mark_dirty()
        self._mode_bar.set_dirty(self._doc.is_dirty())

    def save(self) -> None:
        """The 'Save changes to original file' command."""
        if not self._doc.is_dirty():
            self._report(OpResult(True, strings.MSG_NO_CHANGES))
            return
        self._flush()
        # Announce before writing so a file watcher can ignore our own change.
        self._on_saved()
        result = self._doc.save()
        if result.ok:
            self._mode_bar.set_dirty(False)
        self._report(result)

    def save_as(self, dest: Path) -> OpResult:
        """Write the working copy (with pending edits) to ``dest`` as a new file.

        The original is left untouched; the in-progress edits move to ``dest``,
        so the working copy is discarded and the dirty marker cleared.
        """
        self._flush()
        working = self._doc.working()
        if working is None:
            return OpResult(False, strings.MSG_NO_DOCUMENT)
        try:
            save_copy(working, dest)
        except OSError as err:
            return OpResult(False, str(err))
        self._doc.discard()
        self._mode_bar.set_dirty(False)
        return OpResult(True, file_strings.MSG_SAVED_AS_FMT.format(name=dest.name))

    def discard_unsaved(self) -> None:
        """Abandon pending edits and clear the dirty marker, without prompting.

        For automation/demo runs: lets the app exit without the unsaved-changes
        dialog blocking shutdown.
        """
        self._doc.discard()
        self._mode_bar.set_dirty(False)

    def confirm_unsaved(self) -> bool:
        """Prompt to save pending changes. Return False to abort the caller."""
        if not self._doc.is_dirty():
            return True
        choice = confirm_dialog.confirm(
            self._parent,
            confirm_dialog.ConfirmSpec(
                title=strings.CONFIRM_UNSAVED_TITLE,
                message=strings.CONFIRM_UNSAVED_TEXT,
                primary=strings.BTN_SAVE,
                secondary=strings.BTN_DISCARD,
                cancel=strings.BTN_CANCEL,
            ),
        )
        if choice is confirm_dialog.DialogResult.CANCEL:
            return False
        if choice is confirm_dialog.DialogResult.PRIMARY:
            self._flush()
            self._on_saved()
            result = self._doc.save()
            if not result.ok:
                self._report(result)
                return False
        else:  # Discard: abandon the working edits
            self._doc.discard()
        self._mode_bar.set_dirty(False)
        return True
