"""Integration tests for the 'File type associations…' palette command."""

from __future__ import annotations

import os

import pytest

from app.gui import commands, default_app_actions
from app.gui.confirm_dialog import Severity
from app.gui.main_window import MainWindow
from app.os_integration import file_association
from app.os_integration.file_association import RegistrationResult


def _capture_messages(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, Severity]]:
    """Patch the action's show_message and return the list it records into."""
    shown: list[tuple[str, str, Severity]] = []

    def fake(parent: object, title: str, text: str, severity: Severity = Severity.INFO) -> None:
        shown.append((title, text, severity))

    monkeypatch.setattr(default_app_actions, "show_message", fake)
    return shown


def _capture_startfile(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch os.startfile in the action module; return the recorded URIs."""
    opened: list[str] = []
    monkeypatch.setattr(os, "startfile", lambda uri: opened.append(uri), raising=False)
    return opened


def _result(ok: bool, *, is_windows: bool = True, error: str | None = None) -> RegistrationResult:
    return RegistrationResult(
        ok=ok,
        progid=file_association.PROGID,
        launch_command="cmd",
        is_windows=is_windows,
        error=error,
    )


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    *,
    registered: frozenset[str] = frozenset(),
    selection: frozenset[str] | None = None,
    result: RegistrationResult | None = None,
) -> list[frozenset[str]]:
    """Patch registry + dialog seams; return the set_associations call log."""
    calls: list[frozenset[str]] = []

    def set_associations(checked: frozenset[str]) -> RegistrationResult:
        calls.append(checked)
        return result if result is not None else _result(True)

    monkeypatch.setattr(file_association, "is_supported", lambda: True)
    monkeypatch.setattr(file_association, "registered_extensions", lambda: registered)
    monkeypatch.setattr(file_association, "set_associations", set_associations)
    monkeypatch.setattr(default_app_actions, "ask_associations", lambda *a, **k: selection)
    return calls


def test_command_present_and_old_ids_gone(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.FILE_TYPE_ASSOCIATIONS) is not None
    ids = {command.command_id for command in registry}
    assert "set_default_pdf_viewer" not in ids
    assert "remove_pdf_handler" not in ids


def test_command_enabled_tracks_platform(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(file_association, "is_supported", lambda: True)
    enabled = commands.build_commands(window)
    assert commands.find(enabled, commands.FILE_TYPE_ASSOCIATIONS).is_enabled() is True

    monkeypatch.setattr(file_association, "is_supported", lambda: False)
    disabled = commands.build_commands(window)
    assert commands.find(disabled, commands.FILE_TYPE_ASSOCIATIONS).is_enabled() is False


def test_cancel_touches_nothing(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _wire(monkeypatch, selection=None)
    shown = _capture_messages(monkeypatch)
    opened = _capture_startfile(monkeypatch)

    window.default_app_actions.configure_file_associations()

    assert calls == []
    assert shown == []
    assert opened == []


def test_selection_applies_and_opens_settings(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    selection = frozenset({".pdf", ".md"})
    calls = _wire(monkeypatch, selection=selection)
    shown = _capture_messages(monkeypatch)
    opened = _capture_startfile(monkeypatch)

    window.default_app_actions.configure_file_associations()

    assert calls == [selection]
    assert opened == [f"ms-settings:defaultapps?registeredAppUser={file_association.APP_NAME}"]
    assert shown and shown[-1][2] is Severity.INFO


def test_dialog_prechecked_from_registry(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = frozenset({".png"})
    _wire(monkeypatch, registered=registered, selection=None)
    seen: list[frozenset[str]] = []
    monkeypatch.setattr(
        default_app_actions,
        "ask_associations",
        lambda parent, *, checked: seen.append(checked),
    )

    window.default_app_actions.configure_file_associations()

    assert seen == [registered]


def test_failure_shows_error_and_skips_settings(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    _wire(monkeypatch, selection=frozenset({".pdf"}), result=_result(False, error="x"))
    shown = _capture_messages(monkeypatch)
    opened = _capture_startfile(monkeypatch)

    window.default_app_actions.configure_file_associations()

    assert opened == []
    assert shown and shown[-1][2] is Severity.ERROR


def test_empty_selection_removes_without_settings(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _wire(monkeypatch, registered=frozenset({".pdf"}), selection=frozenset())
    shown = _capture_messages(monkeypatch)
    opened = _capture_startfile(monkeypatch)

    window.default_app_actions.configure_file_associations()

    assert calls == [frozenset()]
    assert opened == []
    assert shown and shown[-1][2] is Severity.INFO


def test_non_windows_warns(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _wire(monkeypatch, selection=frozenset({".pdf"}))
    monkeypatch.setattr(file_association, "is_supported", lambda: False)
    shown = _capture_messages(monkeypatch)

    window.default_app_actions.configure_file_associations()

    assert calls == []
    assert shown and shown[-1][2] is Severity.WARNING
