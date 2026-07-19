"""Unit tests for the int/float prompt dialogs."""

from __future__ import annotations

import pytest

from app.gui.number_input_dialog import (
    NumberInputDialog,
    NumberPromptSpec,
    prompt_float,
    prompt_int,
)


def test_prompt_int_returns_value_on_accept(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(NumberInputDialog, "exec", lambda self: 1)
    assert (
        prompt_int(None, NumberPromptSpec(title="t", label="l", value=5, minimum=0, maximum=10))
        == 5
    )


def test_prompt_int_clamps_to_bounds(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(NumberInputDialog, "exec", lambda self: 1)
    assert (
        prompt_int(None, NumberPromptSpec(title="t", label="l", value=999, minimum=0, maximum=10))
        == 10
    )


def test_prompt_int_returns_none_on_cancel(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(NumberInputDialog, "exec", lambda self: 0)
    assert (
        prompt_int(None, NumberPromptSpec(title="t", label="l", value=5, minimum=0, maximum=10))
        is None
    )


def test_prompt_float_returns_value_on_accept(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(NumberInputDialog, "exec", lambda self: 1)
    assert prompt_float(
        None, NumberPromptSpec(title="t", label="l", value=1.5, minimum=0.0, maximum=10.0)
    ) == pytest.approx(1.5)


def test_prompt_float_returns_none_on_cancel(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(NumberInputDialog, "exec", lambda self: 0)
    assert (
        prompt_float(
            None, NumberPromptSpec(title="t", label="l", value=1.5, minimum=0.0, maximum=10.0)
        )
        is None
    )
