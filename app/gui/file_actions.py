"""Clipboard and open-folder commands for the currently open document."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QWidget

from app.app_logger import log
from app.gui import file_strings, render
from app.gui.operations import OpResult
from app.pdf.words import page_text


class FileActions:
    """Copy the open file's path/name, page text/image, or reveal its folder."""

    def __init__(
        self,
        parent: QWidget,
        source: Callable[[], Path | None],
        report: Callable[[OpResult], None],
        current_page: Callable[[], int],
        grab_view: Callable[[], QPixmap],
    ) -> None:
        self._parent = parent
        self._source = source
        self._report = report
        self._current_page = current_page
        self._grab_view = grab_view

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

    def copy_name_without_extension(self) -> None:
        source = self._source()
        if source is None:
            return
        QGuiApplication.clipboard().setText(source.stem)
        self._report(OpResult(True, file_strings.MSG_COPIED_NAME_NO_EXT))

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

    def copy_page_image(self, scale: float) -> None:
        """Copy the current page rendered at ``scale`` of its original size.

        1.0 is one pixel per PDF point — for image documents the native pixels.
        """
        source = self._source()
        if source is None:
            return
        image = render.render_page(source, self._current_page(), quality=1.0, zoom=scale)
        QGuiApplication.clipboard().setImage(image)
        self._report(OpResult(True, file_strings.MSG_COPIED_PAGE_IMAGE))

    def copy_view_image(self, scale: float = 1.0) -> None:
        if self._source() is None:
            return
        pixmap = self._grab_view()
        if scale != 1.0:
            pixmap = pixmap.scaled(
                max(1, round(pixmap.width() * scale)),
                max(1, round(pixmap.height() * scale)),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        QGuiApplication.clipboard().setPixmap(pixmap)
        self._report(OpResult(True, file_strings.MSG_COPIED_VIEW_IMAGE))

    def open_folder(self) -> None:
        source = self._source()
        if source is None:
            return
        try:
            os.startfile(source.parent)  # noqa: S606
        except OSError as err:
            log.warning("could not open folder: %s", err)
            self._report(OpResult(False, file_strings.MSG_OPEN_FOLDER_FAILED_FMT.format(error=err)))
