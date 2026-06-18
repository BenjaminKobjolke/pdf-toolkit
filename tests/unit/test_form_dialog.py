"""Unit tests for the shared FormDialog skeleton and exec_value helper."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialogButtonBox, QLabel

from app.gui.form_dialog import FormDialog, exec_value


def test_message_renders_as_wordwrapped_label(qapp: object) -> None:
    dialog = FormDialog(title="T", message="hello")
    label = dialog.findChild(QLabel)
    assert label is not None
    assert label.text() == "hello"
    assert label.wordWrap() is True


def test_add_ok_cancel_provides_ok_and_cancel(qapp: object) -> None:
    dialog = FormDialog()
    box = dialog.add_ok_cancel()
    assert box.button(QDialogButtonBox.StandardButton.Ok) is not None
    assert box.button(QDialogButtonBox.StandardButton.Cancel) is not None


def test_exec_value_returns_reader_on_accept(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    dialog = FormDialog()
    monkeypatch.setattr(dialog, "exec", lambda: 1)
    assert exec_value(dialog, lambda: 42) == 42


def test_exec_value_returns_none_on_cancel(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    dialog = FormDialog()
    monkeypatch.setattr(dialog, "exec", lambda: 0)
    assert exec_value(dialog, lambda: 42) is None
