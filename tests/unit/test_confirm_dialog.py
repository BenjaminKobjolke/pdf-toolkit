"""Unit tests for the confirm/alert dialogs."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialogButtonBox, QPushButton

from app.gui import confirm_dialog
from app.gui.confirm_dialog import ConfirmDialog, DialogResult, Severity, show_message


def _click(dialog: ConfirmDialog, text: str) -> None:
    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    for button in box.buttons():
        if button.text() == text:
            button.click()
            return
    raise AssertionError(f"no button labelled {text!r}")


def test_primary_click_returns_primary(qapp: object) -> None:
    dialog = ConfirmDialog(title="T", message="M", primary="Yes", secondary="No")
    _click(dialog, "Yes")
    assert dialog.result_choice() is DialogResult.PRIMARY


def test_secondary_click_returns_secondary(qapp: object) -> None:
    dialog = ConfirmDialog(title="T", message="M", primary="Yes", secondary="No")
    _click(dialog, "No")
    assert dialog.result_choice() is DialogResult.SECONDARY


def test_cancel_click_returns_cancel(qapp: object) -> None:
    dialog = ConfirmDialog(
        title="T", message="M", primary="Save", secondary="Discard", cancel="Cancel"
    )
    _click(dialog, "Cancel")
    assert dialog.result_choice() is DialogResult.CANCEL


def test_esc_returns_cancel_when_cancel_present(qapp: object) -> None:
    dialog = ConfirmDialog(
        title="T", message="M", primary="Save", secondary="Discard", cancel="Cancel"
    )
    dialog.reject()
    assert dialog.result_choice() is DialogResult.CANCEL


def test_esc_returns_secondary_for_two_button(qapp: object) -> None:
    dialog = ConfirmDialog(title="T", message="M", primary="Yes", secondary="No")
    dialog.reject()
    assert dialog.result_choice() is DialogResult.SECONDARY


def test_default_button_is_marked(qapp: object) -> None:
    dialog = ConfirmDialog(
        title="T", message="M", primary="Yes", secondary="No", default=DialogResult.SECONDARY
    )
    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    marked = {b.text() for b in box.buttons() if isinstance(b, QPushButton) and b.isDefault()}
    assert marked == {"No"}


def test_show_message_prepends_severity_prefix(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, str] = {}

    class FakeDialog:
        def __init__(self, **kwargs: str) -> None:
            captured.update(kwargs)

        def exec(self) -> int:
            return 1

    monkeypatch.setattr(confirm_dialog, "ConfirmDialog", FakeDialog)
    show_message(None, "t", "boom", Severity.ERROR)
    assert captured["message"].startswith("✕ ")
    assert captured["message"].endswith("boom")
