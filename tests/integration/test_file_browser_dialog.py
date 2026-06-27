"""Integration tests for the vim-style file browser dialog (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.gui import file_browser_strings as fbs
from app.gui.file_browser_dialog import FileBrowserDialog, _Mode


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """tmp_path with: sub/ (containing deep.pdf), a.pdf, b.pdf, note.txt."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "deep.pdf").write_bytes(b"%PDF")
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    (tmp_path / "b.pdf").write_bytes(b"%PDF")
    (tmp_path / "note.txt").write_text("x")
    return tmp_path


def _send(dialog: FileBrowserDialog, text: str, key: Qt.Key = Qt.Key.Key_unknown) -> None:
    event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, text)
    QApplication.sendEvent(dialog._list, event)


def test_open_picks_file_with_l(qapp: object, tree: Path) -> None:
    # Rows (PDF filter): .., sub/, a.pdf, b.pdf — cursor starts on "..".
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree)
    _send(dialog, "j")  # -> sub/
    _send(dialog, "j")  # -> a.pdf
    _send(dialog, "l")  # pick it
    assert dialog.chosen() == tree / "a.pdf"


def test_open_descends_and_picks(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree)
    _send(dialog, "j")  # -> sub/
    _send(dialog, "l")  # descend
    _send(dialog, "j")  # past "..", onto deep.pdf
    _send(dialog, "", Qt.Key.Key_Return)  # pick
    assert dialog.chosen() == tree / "sub" / "deep.pdf"


def test_g_and_capital_g_jump_to_ends(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree)
    _send(dialog, "G")  # last row -> b.pdf
    _send(dialog, "l")
    assert dialog.chosen() == tree / "b.pdf"


def test_up_row_is_first_and_navigates(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree / "sub")
    assert dialog._list.item(0).text() == ".."
    _send(dialog, "l")  # activate ".." -> up to tree
    assert dialog._path_label.text() == str(tree)


def test_h_goes_up_a_directory(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree / "sub")
    _send(dialog, "h")  # back up to tree
    assert dialog._path_label.text() == str(tree)


def test_alt_up_goes_up_a_directory(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree / "sub")
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.AltModifier, "")
    QApplication.sendEvent(dialog._list, event)
    assert dialog._path_label.text() == str(tree)


def test_up_at_drive_root_shows_drive_list(qapp: object, tmp_path: Path) -> None:
    root = Path(tmp_path.anchor)  # e.g. C:\
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_ALL, start=root)
    _send(dialog, "h")  # at a drive root -> drive list
    assert dialog._path_label.text() == fbs.DRIVES_LABEL
    assert dialog._list.count() >= 1
    assert dialog._drives_view is True


def test_filter_narrows_then_picks(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree)
    _send(dialog, "/")  # open type-ahead
    dialog._filter.setText("b.pdf")  # rows now: .., b.pdf
    _send(dialog, "j")  # past "..", onto b.pdf
    _send(dialog, "l")  # pick
    assert dialog.chosen() == tree / "b.pdf"


def test_escape_cancels(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.OPEN, title="t", filt=fbs.FILTER_PDF, start=tree)
    _send(dialog, "\x1b", Qt.Key.Key_Escape)
    assert dialog.chosen() is None


def test_save_overwrites_highlighted_file(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(
        mode=_Mode.SAVE, title="t", filt=fbs.FILTER_PDF, start=tree, default_name="out.pdf"
    )
    _send(dialog, "j")  # -> sub/
    _send(dialog, "j")  # -> a.pdf
    _send(dialog, "", Qt.Key.Key_Return)  # accept overwrite
    assert dialog.chosen() == tree / "a.pdf"


def test_save_accepts_typed_name(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(
        mode=_Mode.SAVE, title="t", filt=fbs.FILTER_PDF, start=tree, default_name="out.pdf"
    )
    dialog._accept_save()  # typed name in the prefilled field
    assert dialog.chosen() == tree / "out.pdf"


def test_directory_mode_shows_only_dirs_and_accepts_current(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.DIR, title="t", filt=fbs.FILTER_ALL, start=tree)
    assert [dialog._list.item(i).text() for i in range(dialog._list.count())] == ["..", "sub/"]
    _send(dialog, "j")  # off "..", onto sub/
    _send(dialog, "", Qt.Key.Key_Return)  # accept the directory we are browsing
    assert dialog.chosen() == tree


def test_directory_mode_enter_on_subdir_descends(qapp: object, tree: Path) -> None:
    dialog = FileBrowserDialog(mode=_Mode.DIR, title="t", filt=fbs.FILTER_ALL, start=tree)
    _send(dialog, "j")  # off "..", onto sub/
    _send(dialog, "l")  # descend into sub/
    assert dialog._path_label.text() == str(tree / "sub")
