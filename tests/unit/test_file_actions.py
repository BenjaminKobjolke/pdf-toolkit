"""Unit tests for the clipboard file-utility actions (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QWidget

from app.gui import file_strings
from app.gui.file_actions import FileActions
from app.gui.operations import OpResult
from tests.conftest import MakePdf


def _actions(
    source: Path | None, report: MagicMock, grab_view: MagicMock | None = None
) -> FileActions:
    parent = MagicMock(spec=QWidget)
    return FileActions(
        parent,
        MagicMock(return_value=source),
        report,
        MagicMock(return_value=0),
        grab_view or MagicMock(return_value=QPixmap()),
    )


def test_copy_path_writes_full_path(qapp: object, tmp_path: Path) -> None:
    report = MagicMock()
    source = tmp_path / "report.pdf"
    _actions(source, report).copy_path()

    assert QGuiApplication.clipboard().text() == str(source)
    report.assert_called_once_with(OpResult(True, file_strings.MSG_COPIED_PATH))


def test_copy_name_writes_name_with_extension(qapp: object, tmp_path: Path) -> None:
    report = MagicMock()
    _actions(tmp_path / "report.pdf", report).copy_name()

    assert QGuiApplication.clipboard().text() == "report.pdf"
    report.assert_called_once_with(OpResult(True, file_strings.MSG_COPIED_NAME))


def test_copy_name_without_extension_writes_stem(qapp: object, tmp_path: Path) -> None:
    report = MagicMock()
    _actions(tmp_path / "report.pdf", report).copy_name_without_extension()

    assert QGuiApplication.clipboard().text() == "report"
    report.assert_called_once_with(OpResult(True, file_strings.MSG_COPIED_NAME_NO_EXT))


def test_copy_name_without_extension_no_source_does_nothing(qapp: object) -> None:
    report = MagicMock()
    QGuiApplication.clipboard().setText("untouched")
    _actions(None, report).copy_name_without_extension()

    assert QGuiApplication.clipboard().text() == "untouched"
    report.assert_not_called()


def test_copy_page_image_full_scale_is_one_pixel_per_point(qapp: object, make_pdf: MakePdf) -> None:
    report = MagicMock()
    _actions(make_pdf([(200, 100)]), report).copy_page_image(1.0)

    image = QGuiApplication.clipboard().image()
    assert (image.width(), image.height()) == (200, 100)
    report.assert_called_once_with(OpResult(True, file_strings.MSG_COPIED_PAGE_IMAGE))


def test_copy_page_image_quarter_scale(qapp: object, make_pdf: MakePdf) -> None:
    report = MagicMock()
    _actions(make_pdf([(200, 100)]), report).copy_page_image(0.25)

    image = QGuiApplication.clipboard().image()
    assert abs(image.width() - 50) <= 1
    assert abs(image.height() - 25) <= 1


def test_copy_page_image_no_source_does_nothing(qapp: object) -> None:
    report = MagicMock()
    QGuiApplication.clipboard().setText("untouched")
    _actions(None, report).copy_page_image(1.0)

    assert QGuiApplication.clipboard().text() == "untouched"
    report.assert_not_called()


def test_copy_view_image_puts_grabbed_pixmap_on_clipboard(qapp: object, tmp_path: Path) -> None:
    report = MagicMock()
    grab = MagicMock(return_value=QPixmap(12, 34))
    _actions(tmp_path / "report.pdf", report, grab).copy_view_image()

    pixmap = QGuiApplication.clipboard().pixmap()
    assert (pixmap.width(), pixmap.height()) == (12, 34)
    report.assert_called_once_with(OpResult(True, file_strings.MSG_COPIED_VIEW_IMAGE))


def test_copy_view_image_half_scale_halves_pixmap(qapp: object, tmp_path: Path) -> None:
    report = MagicMock()
    grab = MagicMock(return_value=QPixmap(100, 40))
    _actions(tmp_path / "report.pdf", report, grab).copy_view_image(0.5)

    pixmap = QGuiApplication.clipboard().pixmap()
    assert (pixmap.width(), pixmap.height()) == (50, 20)
    report.assert_called_once_with(OpResult(True, file_strings.MSG_COPIED_VIEW_IMAGE))


def test_copy_view_image_quarter_scale(qapp: object, tmp_path: Path) -> None:
    report = MagicMock()
    grab = MagicMock(return_value=QPixmap(100, 40))
    _actions(tmp_path / "report.pdf", report, grab).copy_view_image(0.25)

    pixmap = QGuiApplication.clipboard().pixmap()
    assert (pixmap.width(), pixmap.height()) == (25, 10)
