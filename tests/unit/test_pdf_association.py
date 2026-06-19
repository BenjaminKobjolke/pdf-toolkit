"""Unit tests for the Windows PDF-handler registration module.

A fake ``winreg`` is injected into the module so the real registry is never
touched; the tests assert which keys/values would be written.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.os_integration import pdf_association
from app.os_integration.pdf_association import RegistrationResult


class _FakeKey:
    """Stand-in for a registry key handle that records its subkey."""

    def __init__(self, subkey: str) -> None:
        self.subkey = subkey

    def __enter__(self) -> _FakeKey:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


class FakeWinreg:
    """Minimal in-memory ``winreg`` recording all write/delete calls."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_WRITE = 0x20006
    REG_SZ = 1
    REG_NONE = 0

    def __init__(self) -> None:
        self.created: list[str] = []
        self.values: list[tuple[str, str, int, object]] = []
        self.opened: list[str] = []
        self.deleted_keys: list[str] = []
        self.deleted_values: list[tuple[str, str]] = []
        self.fail: Exception | None = None

    def CreateKeyEx(self, root: str, subkey: str, reserved: int, access: int) -> _FakeKey:
        if self.fail is not None:
            raise self.fail
        self.created.append(subkey)
        return _FakeKey(subkey)

    def OpenKey(self, root: str, subkey: str, reserved: int, access: int) -> _FakeKey:
        if self.fail is not None:
            raise self.fail
        self.opened.append(subkey)
        return _FakeKey(subkey)

    def SetValueEx(self, key: _FakeKey, name: str, reserved: int, type_: int, data: object) -> None:
        self.values.append((key.subkey, name, type_, data))

    def DeleteKey(self, root: str, subkey: str) -> None:
        self.deleted_keys.append(subkey)

    def DeleteValue(self, key: _FakeKey, name: str) -> None:
        self.deleted_values.append((key.subkey, name))


@pytest.fixture
def fake_winreg(monkeypatch: pytest.MonkeyPatch) -> FakeWinreg:
    """Replace the module's ``winreg`` with a recording fake; force Windows."""
    fake = FakeWinreg()
    monkeypatch.setattr(pdf_association, "winreg", fake)
    monkeypatch.setattr(pdf_association.sys, "platform", "win32")
    monkeypatch.setattr(pdf_association.sys, "frozen", False, raising=False)
    return fake


def _with_vbs(tmp_path: Path) -> Path:
    """Return ``tmp_path`` after creating a dummy launcher vbs in it."""
    (tmp_path / pdf_association.LAUNCHER_VBS).write_text("' launcher")
    return tmp_path


def test_is_supported_tracks_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_association.sys, "platform", "win32")
    assert pdf_association.is_supported() is True
    monkeypatch.setattr(pdf_association.sys, "platform", "linux")
    assert pdf_association.is_supported() is False


def test_launch_command_dev_points_at_vbs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pdf_association.sys, "frozen", False, raising=False)
    vbs = tmp_path / pdf_association.LAUNCHER_VBS
    assert pdf_association.launch_command(tmp_path) == f'wscript.exe "{vbs}" "%1"'


def test_launch_command_frozen_points_at_exe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_association.sys, "frozen", True, raising=False)
    monkeypatch.setattr(pdf_association.sys, "executable", r"C:\apps\FastPDFToolkit.exe")
    assert pdf_association.launch_command() == r'"C:\apps\FastPDFToolkit.exe" "%1"'


def test_register_writes_all_keys(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    root = _with_vbs(tmp_path)
    result = pdf_association.register_pdf_viewer(root)

    assert result.ok is True
    assert result.is_windows is True
    assert result.progid == pdf_association.PROGID
    # ProgID label, icon, command, plus the OpenWithProgids container.
    assert pdf_association.PROGID_KEY in fake_winreg.created
    assert pdf_association.ICON_KEY in fake_winreg.created
    assert pdf_association.COMMAND_KEY in fake_winreg.created
    assert pdf_association.OPENWITH_KEY in fake_winreg.created

    values = {(sub, name): (type_, data) for sub, name, type_, data in fake_winreg.values}
    assert values[(pdf_association.PROGID_KEY, "")] == (
        FakeWinreg.REG_SZ,
        pdf_association.PROGID_LABEL,
    )
    assert values[(pdf_association.ICON_KEY, "")] == (
        FakeWinreg.REG_SZ,
        pdf_association.PROGID_ICON,
    )
    assert values[(pdf_association.COMMAND_KEY, "")] == (
        FakeWinreg.REG_SZ,
        result.launch_command,
    )
    # The 'Open with' entry: a REG_NONE value named after the ProgID.
    assert values[(pdf_association.OPENWITH_KEY, pdf_association.PROGID)][0] == FakeWinreg.REG_NONE


def test_register_is_idempotent(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    root = _with_vbs(tmp_path)
    first = pdf_association.register_pdf_viewer(root)
    before = len(fake_winreg.values)
    second = pdf_association.register_pdf_viewer(root)
    assert first.ok and second.ok
    # Second run writes the same number of values again (overwrite, no error).
    assert len(fake_winreg.values) == before * 2


def test_register_missing_vbs_writes_nothing(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    result = pdf_association.register_pdf_viewer(tmp_path)  # no vbs created
    assert result.ok is False
    assert fake_winreg.values == []
    assert fake_winreg.created == []


def test_register_swallows_oserror(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    fake_winreg.fail = OSError("access denied")
    result = pdf_association.register_pdf_viewer(_with_vbs(tmp_path))
    assert result.ok is False
    assert result.error is not None
    assert "access denied" in result.error


def test_register_non_windows_touches_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake = FakeWinreg()
    monkeypatch.setattr(pdf_association, "winreg", fake)
    monkeypatch.setattr(pdf_association.sys, "platform", "linux")
    result = pdf_association.register_pdf_viewer(_with_vbs(tmp_path))
    assert result == RegistrationResult(
        ok=False,
        progid=pdf_association.PROGID,
        launch_command=result.launch_command,
        is_windows=False,
        error=result.error,
    )
    assert result.is_windows is False
    assert fake.values == []


def test_unregister_deletes_keys_and_value(fake_winreg: FakeWinreg) -> None:
    result = pdf_association.unregister_pdf_viewer()
    assert result.ok is True
    # The ProgID tree key is removed and the OpenWithProgids value cleared.
    assert pdf_association.PROGID_KEY in fake_winreg.deleted_keys
    assert (pdf_association.OPENWITH_KEY, pdf_association.PROGID) in fake_winreg.deleted_values


def test_unregister_non_windows_touches_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeWinreg()
    monkeypatch.setattr(pdf_association, "winreg", fake)
    monkeypatch.setattr(pdf_association.sys, "platform", "linux")
    result = pdf_association.unregister_pdf_viewer()
    assert result.ok is False
    assert result.is_windows is False
    assert fake.deleted_keys == []
