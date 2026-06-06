"""Unit tests for GUI resource helpers."""

from __future__ import annotations

import sys

import pytest

from app.gui import resources


def test_set_app_user_model_id_noop_off_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    assert resources.set_app_user_model_id() is False


def test_set_app_user_model_id_calls_shell32_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    seen: list[str] = []

    class _Shell32:
        def SetCurrentProcessExplicitAppUserModelID(self, app_id: str) -> int:  # noqa: N802
            seen.append(app_id)
            return 0

    class _Windll:
        shell32 = _Shell32()

    import ctypes

    monkeypatch.setattr(ctypes, "windll", _Windll(), raising=False)

    assert resources.set_app_user_model_id("Acme.App") is True
    assert seen == ["Acme.App"]
