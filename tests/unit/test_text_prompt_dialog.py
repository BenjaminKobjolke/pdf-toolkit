"""Unit tests for the single-line text prompt dialog."""

from __future__ import annotations

import pytest

from app.gui.text_prompt_dialog import TextPromptDialog, prompt_text


def test_returns_trimmed_text_on_accept(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TextPromptDialog, "exec", lambda self: 1)
    assert prompt_text(None, "t", "l", "  hi  ") == "hi"


def test_empty_after_trim_returns_none(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TextPromptDialog, "exec", lambda self: 1)
    assert prompt_text(None, "t", "l", "   ") is None


def test_cancel_returns_none(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TextPromptDialog, "exec", lambda self: 0)
    assert prompt_text(None, "t", "l", "hi") is None


def test_select_all_false_places_caret_at_end(qapp: object) -> None:
    dialog = TextPromptDialog(title="t", label="l", text="abc", select_all=False)
    assert dialog._edit.cursorPosition() == 3
    assert not dialog._edit.hasSelectedText()
