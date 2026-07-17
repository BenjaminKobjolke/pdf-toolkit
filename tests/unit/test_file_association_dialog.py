"""Unit tests for the file-type association checklist dialog."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from app.gui.file_association_dialog import FileAssociationDialog
from app.pdf.file_format import FileFormat


def _press_space(dialog: FileAssociationDialog) -> None:
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
    dialog._list.keyPressEvent(event)


def test_lists_every_file_format(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    assert dialog._list.count() == len(FileFormat)


def test_prechecks_given_extensions(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset({".pdf", ".md"}))
    assert dialog.selected() == frozenset({".pdf", ".md"})


def test_nothing_checked_by_default(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    assert dialog.selected() == frozenset()


def test_toggling_an_item_updates_selection(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    item = dialog._list.item(0)  # enum order: .pdf first
    item.setCheckState(Qt.CheckState.Checked)
    assert ".pdf" in dialog.selected()
    item.setCheckState(Qt.CheckState.Unchecked)
    assert dialog.selected() == frozenset()


def test_labels_show_extension_and_kind(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    labels = [dialog._list.item(i).text() for i in range(dialog._list.count())]
    assert any(label.startswith(".pdf") for label in labels)
    assert all("—" in label for label in labels)


def test_items_are_selectable_for_keyboard_navigation(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    for i in range(dialog._list.count()):
        assert dialog._list.item(i).flags() & Qt.ItemFlag.ItemIsSelectable


def test_list_has_initial_current_row(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    assert dialog._list.currentRow() == 0


def test_space_toggles_current_item(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    dialog._list.setCurrentRow(0)  # enum order: .pdf first
    _press_space(dialog)
    assert ".pdf" in dialog.selected()
    _press_space(dialog)
    assert dialog.selected() == frozenset()


def test_select_all_checks_everything(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset())
    dialog._select_all.click()
    assert dialog.selected() == frozenset(f.value for f in FileFormat)


def test_unselect_all_clears_everything(qapp: object) -> None:
    dialog = FileAssociationDialog(checked=frozenset({".pdf", ".md"}))
    dialog._unselect_all.click()
    assert dialog.selected() == frozenset()
