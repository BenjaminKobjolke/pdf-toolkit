"""Unit tests for the running-process enumerator."""

from __future__ import annotations

import sys
from pathlib import Path

import psutil
import pytest

from app.os_integration import processes
from app.os_integration.processes import RunningApp, running_apps


class _FakeProc:
    def __init__(self, info: dict[str, object] | Exception) -> None:
        self._info = info

    @property
    def info(self) -> dict[str, object]:
        if isinstance(self._info, Exception):
            raise self._info
        return self._info


def test_dedups_by_path_and_sorts_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    procs = [
        _FakeProc({"name": "Zed", "exe": r"C:\apps\zed.exe"}),
        _FakeProc({"name": "Gimp", "exe": r"C:\apps\gimp.exe"}),
        _FakeProc({"name": "Gimp", "exe": r"C:\apps\gimp.exe"}),  # duplicate path
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda attrs: procs)
    result = running_apps()
    assert result == [
        RunningApp("Gimp", Path(r"C:\apps\gimp.exe")),
        RunningApp("Zed", Path(r"C:\apps\zed.exe")),
    ]


def test_skips_no_exe_and_inaccessible(monkeypatch: pytest.MonkeyPatch) -> None:
    procs = [
        _FakeProc({"name": "System", "exe": None}),  # kernel process, no exe
        _FakeProc({"name": "", "exe": ""}),  # empty exe
        _FakeProc(psutil.AccessDenied()),  # no rights to read
        _FakeProc(psutil.NoSuchProcess(1)),  # gone mid-iteration
        _FakeProc({"name": "Ok", "exe": r"C:\apps\ok.exe"}),
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda attrs: procs)
    assert running_apps() == [RunningApp("Ok", Path(r"C:\apps\ok.exe"))]


def test_falls_back_to_stem_when_name_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        psutil, "process_iter", lambda attrs: [_FakeProc({"name": None, "exe": r"C:\a\Foo.exe"})]
    )
    assert running_apps() == [RunningApp("Foo", Path(r"C:\a\Foo.exe"))]


def test_real_enumeration_includes_this_interpreter() -> None:
    # Smoke test against real psutil: the running Python must be listed.
    apps = processes.running_apps()
    assert isinstance(apps, list)
    this_exe = Path(sys.executable)
    assert any(app.path == this_exe for app in apps)
