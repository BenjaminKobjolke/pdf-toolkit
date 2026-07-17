"""Unit tests for the Windows file-type association module.

A fake in-memory ``winreg`` is injected into the module so the real registry
is never touched; the tests assert the declarative end state (what a read-back
would see), not just the call sequence.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import pytest

from app.os_integration import file_association


class _FakeKey:
    """Stand-in for a registry key handle that records its subkey."""

    def __init__(self, subkey: str) -> None:
        self.subkey = subkey

    def __enter__(self) -> _FakeKey:
        return self

    def __exit__(self, *_args: object) -> Literal[False]:
        return False


class FakeWinreg:
    """In-memory ``winreg``: subkey path -> {value name: (type, data)}."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_WRITE = 0x20006
    KEY_READ = 0x20019
    REG_SZ = 1
    REG_NONE = 0

    def __init__(self) -> None:
        self.keys: dict[str, dict[str, tuple[int, object]]] = {}
        self.fail: Exception | None = None

    def CreateKeyEx(self, root: str, subkey: str, reserved: int, access: int) -> _FakeKey:
        if self.fail is not None:
            raise self.fail
        self.keys.setdefault(subkey, {})
        return _FakeKey(subkey)

    def OpenKey(self, root: str, subkey: str, reserved: int = 0, access: int = 0) -> _FakeKey:
        if self.fail is not None:
            raise self.fail
        if subkey not in self.keys:
            raise FileNotFoundError(subkey)
        return _FakeKey(subkey)

    def SetValueEx(self, key: _FakeKey, name: str, reserved: int, type_: int, data: object) -> None:
        self.keys[key.subkey][name] = (type_, data)

    def QueryValueEx(self, key: _FakeKey, name: str) -> tuple[object, int]:
        try:
            type_, data = self.keys[key.subkey][name]
        except KeyError:
            raise FileNotFoundError(name) from None
        return (data, type_)

    def DeleteKey(self, root: str, subkey: str) -> None:
        if subkey not in self.keys:
            raise FileNotFoundError(subkey)
        del self.keys[subkey]

    def DeleteValue(self, key: _FakeKey, name: str) -> None:
        try:
            del self.keys[key.subkey][name]
        except KeyError:
            raise FileNotFoundError(name) from None


@pytest.fixture
def fake_winreg(monkeypatch: pytest.MonkeyPatch) -> FakeWinreg:
    """Replace the module's ``winreg`` with the in-memory fake; force Windows."""
    fake = FakeWinreg()
    monkeypatch.setattr(file_association, "winreg", fake)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    return fake


def _with_vbs(tmp_path: Path) -> Path:
    """Return ``tmp_path`` after creating a dummy launcher vbs in it."""
    (tmp_path / file_association.LAUNCHER_VBS).write_text("' launcher")
    return tmp_path


def _openwith_key(ext: str) -> str:
    return rf"Software\Classes\{ext}\OpenWithProgids"


def test_is_supported_tracks_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    assert file_association.is_supported() is True
    monkeypatch.setattr(sys, "platform", "linux")
    assert file_association.is_supported() is False


def test_launch_command_dev_points_at_vbs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    vbs = tmp_path / file_association.LAUNCHER_VBS
    assert file_association.launch_command(tmp_path) == f'wscript.exe "{vbs}" "%1"'


def test_launch_command_frozen_points_at_exe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\apps\FastFileViewer.exe")
    assert file_association.launch_command() == r'"C:\apps\FastFileViewer.exe" "%1"'


def test_all_extensions_cover_every_file_format() -> None:
    from app.pdf.file_format import FileFormat

    assert set(file_association.ALL_EXTENSIONS) == {f.value for f in FileFormat}


def test_set_associations_writes_progid_and_open_with(
    fake_winreg: FakeWinreg, tmp_path: Path
) -> None:
    result = file_association.set_associations({".pdf", ".png"}, _with_vbs(tmp_path))

    assert result.ok is True
    assert result.is_windows is True
    assert result.progid == file_association.PROGID

    progid_values = fake_winreg.keys[file_association.PROGID_KEY]
    assert progid_values[""] == (FakeWinreg.REG_SZ, file_association.PROGID_LABEL)
    assert fake_winreg.keys[file_association.ICON_KEY][""][1] == file_association.PROGID_ICON
    assert fake_winreg.keys[file_association.COMMAND_KEY][""][1] == result.launch_command
    for ext in (".pdf", ".png"):
        assert file_association.PROGID in fake_winreg.keys[_openwith_key(ext)]


def test_set_associations_registers_app_capabilities(
    fake_winreg: FakeWinreg, tmp_path: Path
) -> None:
    file_association.set_associations({".pdf", ".md"}, _with_vbs(tmp_path))

    caps = fake_winreg.keys[file_association.CAPABILITIES_KEY]
    assert caps["ApplicationName"][1] == file_association.APP_NAME
    assert "ApplicationDescription" in caps
    assoc = fake_winreg.keys[file_association.FILE_ASSOC_KEY]
    assert assoc[".pdf"][1] == file_association.PROGID
    assert assoc[".md"][1] == file_association.PROGID
    registered = fake_winreg.keys[file_association.REGISTERED_APPS_KEY]
    assert registered[file_association.APP_NAME][1] == file_association.CAPABILITIES_KEY


def test_unchecked_extension_is_unregistered(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    root = _with_vbs(tmp_path)
    file_association.set_associations({".pdf", ".png"}, root)
    file_association.set_associations({".pdf"}, root)

    assert file_association.PROGID in fake_winreg.keys[_openwith_key(".pdf")]
    assert file_association.PROGID not in fake_winreg.keys.get(_openwith_key(".png"), {})
    assoc = fake_winreg.keys[file_association.FILE_ASSOC_KEY]
    assert ".pdf" in assoc
    assert ".png" not in assoc


def test_empty_selection_tears_everything_down(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    file_association.set_associations(file_association.ALL_EXTENSIONS, _with_vbs(tmp_path))
    result = file_association.set_associations(frozenset())

    assert result.ok is True
    assert file_association.PROGID_KEY not in fake_winreg.keys
    assert file_association.CAPABILITIES_KEY not in fake_winreg.keys
    assert file_association.FILE_ASSOC_KEY not in fake_winreg.keys
    assert file_association.APP_NAME not in fake_winreg.keys.get(
        file_association.REGISTERED_APPS_KEY, {}
    )
    for ext in file_association.ALL_EXTENSIONS:
        assert file_association.PROGID not in fake_winreg.keys.get(_openwith_key(ext), {})


def test_registered_extensions_round_trip(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    file_association.set_associations({".pdf", ".md"}, _with_vbs(tmp_path))
    assert file_association.registered_extensions() == frozenset({".pdf", ".md"})


def test_registered_extensions_empty_on_fresh_registry(fake_winreg: FakeWinreg) -> None:
    assert file_association.registered_extensions() == frozenset()


def test_registered_extensions_empty_off_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    assert file_association.registered_extensions() == frozenset()


def test_foreign_progids_survive(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    fake_winreg.keys[_openwith_key(".pdf")] = {"Foreign.Viewer": (FakeWinreg.REG_NONE, b"")}
    root = _with_vbs(tmp_path)
    file_association.set_associations({".pdf"}, root)
    file_association.set_associations(frozenset())
    assert "Foreign.Viewer" in fake_winreg.keys[_openwith_key(".pdf")]


def test_set_associations_is_idempotent(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    root = _with_vbs(tmp_path)
    first = file_association.set_associations({".pdf"}, root)
    second = file_association.set_associations({".pdf"}, root)
    assert first.ok and second.ok
    assert file_association.registered_extensions() == frozenset({".pdf"})


def test_non_windows_touches_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = FakeWinreg()
    monkeypatch.setattr(file_association, "winreg", fake)
    monkeypatch.setattr(sys, "platform", "linux")
    result = file_association.set_associations({".pdf"}, _with_vbs(tmp_path))
    assert result.ok is False
    assert result.is_windows is False
    assert fake.keys == {}


def test_oserror_is_swallowed(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    fake_winreg.fail = OSError("access denied")
    result = file_association.set_associations({".pdf"}, _with_vbs(tmp_path))
    assert result.ok is False
    assert result.error is not None
    assert "access denied" in result.error


def test_missing_vbs_blocks_register(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    result = file_association.set_associations({".pdf"}, tmp_path)  # no vbs created
    assert result.ok is False
    assert fake_winreg.keys == {}


def test_missing_vbs_still_allows_removal(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    file_association.set_associations({".pdf"}, _with_vbs(tmp_path))
    result = file_association.set_associations(frozenset(), tmp_path)  # vbs gone is fine
    assert result.ok is True
    assert file_association.registered_extensions() == frozenset()


def test_cli_register_and_unregister(fake_winreg: FakeWinreg, tmp_path: Path) -> None:
    root = _with_vbs(tmp_path)
    assert file_association._main(["register"], root) == 0
    assert file_association.registered_extensions() == frozenset(file_association.ALL_EXTENSIONS)
    assert file_association._main(["unregister"], root) == 0
    assert file_association.registered_extensions() == frozenset()


def test_cli_rejects_unknown_verb(fake_winreg: FakeWinreg) -> None:
    assert file_association._main(["bogus"]) == 2
