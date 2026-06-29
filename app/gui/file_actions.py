"""Clipboard and open-folder commands for the currently open document."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from app.gui import file_strings
from app.gui.operations import OpResult
from app.logging_setup import log
from app.pdf.words import page_text


class FileActions:
    """Copy the open file's path/name or current page text, or reveal its folder."""

    def __init__(
        self,
        parent: QWidget,
        source: Callable[[], Path | None],
        report: Callable[[OpResult], None],
        current_page: Callable[[], int],
    ) -> None:
        self._parent = parent
        self._source = source
        self._report = report
        self._current_page = current_page

    def copy_path(self) -> None:
        source = self._source()
        if source is None:
            return
        QGuiApplication.clipboard().setText(str(source))
        self._report(OpResult(True, file_strings.MSG_COPIED_PATH))

    def copy_name(self) -> None:
        source = self._source()
        if source is None:
            return
        QGuiApplication.clipboard().setText(source.name)
        self._report(OpResult(True, file_strings.MSG_COPIED_NAME))

    def copy_page_text(self) -> None:
        source = self._source()
        if source is None:
            return
        text = page_text(source, self._current_page())
        if not text:
            self._report(OpResult(False, file_strings.MSG_NO_PAGE_TEXT))
            return
        QGuiApplication.clipboard().setText(text)
        self._report(OpResult(True, file_strings.MSG_COPIED_PAGE_TEXT))

    def open_folder(self) -> None:
        source = self._source()
        if source is None:
            return
        try:
            os.startfile(source.parent)  # noqa: S606
        except OSError as err:
            log.warning("could not open folder: %s", err)
            self._report(OpResult(False, file_strings.MSG_OPEN_FOLDER_FAILED_FMT.format(error=err)))
