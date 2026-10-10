"""Tests for environment-driven application settings."""

from __future__ import annotations

import pytest

from app.config.settings import ENV_WATCHER_COMMAND_RUN, Settings


def test_watcher_command_run_is_true_for_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_WATCHER_COMMAND_RUN, "1")

    assert Settings.from_env().watcher_command_run is True


@pytest.mark.parametrize("value", [None, "0", "true", "yes"])
def test_watcher_command_run_is_false_unless_one(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(ENV_WATCHER_COMMAND_RUN, raising=False)
    else:
        monkeypatch.setenv(ENV_WATCHER_COMMAND_RUN, value)

    assert Settings.from_env().watcher_command_run is False
