"""Integration tests for the 'Set as default PDF viewer' palette commands."""

from __future__ import annotations

import pytest

from app.gui import commands, default_app_actions
from app.gui.confirm_dialog import Severity
from app.gui.main_window import MainWindow
from app.os_integration import pdf_association
from app.os_integration.pdf_association import RegistrationResult


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
    monkeypatch.setattr(
        default_app_actions.os, "startfile", lambda uri: opened.append(uri), raising=False
    )
    return opened


def _result(ok: bool, *, is_windows: bool = True, error: str | None = None) -> RegistrationResult:
    return RegistrationResult(
        ok=ok,
        progid=pdf_association.PROGID,
        launch_command="cmd",
        is_windows=is_windows,
        error=error,
    )


def test_commands_present(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.SET_DEFAULT_PDF_VIEWER) is not None
    assert commands.find(registry, commands.REMOVE_PDF_HANDLER) is not None


def test_commands_enabled_tracks_platform(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pdf_association, "is_supported", lambda: True)
    enabled = commands.build_commands(window)
    assert commands.find(enabled, commands.SET_DEFAULT_PDF_VIEWER).is_enabled() is True

    monkeypatch.setattr(pdf_association, "is_supported", lambda: False)
    disabled = commands.build_commands(window)
    assert commands.find(disabled, commands.SET_DEFAULT_PDF_VIEWER).is_enabled() is False


def test_set_default_success_opens_settings(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pdf_association, "is_supported", lambda: True)
    calls: list[str] = []
    monkeypatch.setattr(
        pdf_association, "register_pdf_viewer", lambda *a, **k: calls.append("reg") or _result(True)
    )
    opened = _capture_startfile(monkeypatch)
    shown = _capture_messages(monkeypatch)

    window.default_app_actions.set_as_default_pdf_viewer()

    assert calls == ["reg"]
    assert opened == ["ms-settings:defaultapps"]
    assert shown and shown[-1][2] is Severity.INFO


def test_set_default_failure_skips_settings(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pdf_association, "is_supported", lambda: True)
    monkeypatch.setattr(
        pdf_association, "register_pdf_viewer", lambda *a, **k: _result(False, error="x")
    )
    opened = _capture_startfile(monkeypatch)
    shown = _capture_messages(monkeypatch)

    window.default_app_actions.set_as_default_pdf_viewer()

    assert opened == []
    assert shown and shown[-1][2] is Severity.ERROR


def test_set_default_non_windows_warns(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_association, "is_supported", lambda: False)
    calls: list[str] = []
    monkeypatch.setattr(pdf_association, "register_pdf_viewer", lambda *a, **k: calls.append("reg"))
    shown = _capture_messages(monkeypatch)

    window.default_app_actions.set_as_default_pdf_viewer()

    assert calls == []
    assert shown and shown[-1][2] is Severity.WARNING


def test_remove_handler_success(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_association, "is_supported", lambda: True)
    monkeypatch.setattr(pdf_association, "unregister_pdf_viewer", lambda: _result(True))
    shown = _capture_messages(monkeypatch)

    window.default_app_actions.remove_pdf_handler()

    assert shown and shown[-1][2] is Severity.INFO
