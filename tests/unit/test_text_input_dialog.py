"""Unit tests for the multi-line text input dialog (offscreen Qt)."""

from __future__ import annotations

from app.gui.text_input_dialog import TextInputDialog


def test_prefills_initial_text(qapp: object) -> None:
    dialog = TextInputDialog(initial="hello")
    assert dialog.text() == "hello"


def test_ctrl_enter_accepts(qapp: object) -> None:
    dialog = TextInputDialog(initial="line one")
    dialog.set_text("line one\nline two")
    dialog.submit()  # what Ctrl+Enter triggers
    assert dialog.result() == TextInputDialog.DialogCode.Accepted
    assert dialog.text() == "line one\nline two"


def test_multiline_text_preserved(qapp: object) -> None:
    dialog = TextInputDialog(initial="")
    dialog.set_text("a\nb\nc")
    assert dialog.text() == "a\nb\nc"
