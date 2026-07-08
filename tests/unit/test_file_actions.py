"""Unit tests for the clipboard file-utility actions (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from app.gui import file_strings
from app.gui.file_actions import FileActions
from app.gui.operations import OpResult


def _actions(source: Path | None, report: MagicMock) -> FileActions:
    parent = MagicMock(spec=QWidget)
    return FileActions(parent, MagicMock(return_value=source), report, MagicMock(return_value=0))


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
