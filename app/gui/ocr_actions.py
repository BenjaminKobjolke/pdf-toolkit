"""The OCR-image command: recognize text, then copy it or save it as a sidecar .txt.

Reads the image file on disk (unsaved in-memory rotations are not reflected),
which also makes the command work on the selected thumbnail while the grid
shows — the injected ``source`` callable resolves the effective target.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from app.gui import confirm_dialog, filter_list_dialog, ocr_strings, strings
from app.gui.operations import OpResult
from app.ocr.provider import OcrError
from app.pdf._atomic import write_text_atomic

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from PySide6.QtWidgets import QWidget

    from app.ocr.provider import OcrProvider


class _Destination(Enum):
    CLIPBOARD = auto()
    FILE = auto()


class OcrActions:
    """Run OCR on the effective image file and hand the text to the user."""

    def __init__(
        self,
        parent: QWidget,
        provider: OcrProvider,
        source: Callable[[], Path | None],
        report: Callable[[OpResult], None],
        language: Callable[[], str | None],
    ) -> None:
        self._parent = parent
        self._provider = provider
        self._source = source
        self._report = report
        self._language = language

    def recognize(self) -> None:
        source = self._source()
        if source is None:
            return
        if not self._provider.is_available():
            self._report(OpResult(False, ocr_strings.MSG_OCR_UNAVAILABLE))
            return
        text = self._run_engine(source)
        if text is None:
            return
        if not text.strip():
            self._report(OpResult(False, ocr_strings.MSG_OCR_NO_TEXT))
            return
        self._deliver(text, source.with_suffix(".txt"))

    def _run_engine(self, source: Path) -> str | None:
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            return self._provider.recognize(source, self._language())
        except OcrError as err:
            self._report(OpResult(False, ocr_strings.MSG_OCR_FAILED_FMT.format(error=err)))
            return None
        finally:
            QGuiApplication.restoreOverrideCursor()

    def _deliver(self, text: str, target: Path) -> None:
        choice = filter_list_dialog.pick_option(
            self._parent,
            {
                _Destination.CLIPBOARD: ocr_strings.OPT_COPY,
                _Destination.FILE: ocr_strings.OPT_SAVE_FMT.format(name=target.name),
            },
            title=ocr_strings.PICK_TITLE,
            placeholder=ocr_strings.PICK_PLACEHOLDER,
        )
        if choice is _Destination.CLIPBOARD:
            QGuiApplication.clipboard().setText(text)
            self._report(OpResult(True, ocr_strings.MSG_OCR_COPIED))
        elif choice is _Destination.FILE:
            self._save(text, target)

    def _save(self, text: str, target: Path) -> None:
        if target.exists():
            spec = confirm_dialog.ConfirmSpec(
                title=ocr_strings.CONFIRM_OVERWRITE_TITLE,
                message=ocr_strings.CONFIRM_OVERWRITE_FMT.format(name=target.name),
                primary=strings.BTN_YES,
                secondary=strings.BTN_NO,
            )
            choice = confirm_dialog.confirm(self._parent, spec)
            if choice is not confirm_dialog.DialogResult.PRIMARY:
                return
        write_text_atomic(target, text)
        self._report(OpResult(True, ocr_strings.MSG_OCR_SAVED_FMT.format(name=target.name)))
