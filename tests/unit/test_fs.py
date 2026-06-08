"""Unit tests for app.io.fs (read-only-safe atomic replace)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from app.io.fs import clear_readonly, replace_atomic


def test_replace_atomic_overwrites_readonly_destination(tmp_path: Path) -> None:
    dst = tmp_path / "target.bin"
    dst.write_bytes(b"old")
    os.chmod(dst, stat.S_IREAD)  # mark read-only (WinError 5 trigger on os.replace)

    tmp = tmp_path / "target.bin.tmp"
    tmp.write_bytes(b"new")

    replace_atomic(tmp, dst)

    assert dst.read_bytes() == b"new"
    assert not tmp.exists()


def test_replace_atomic_creates_when_destination_absent(tmp_path: Path) -> None:
    dst = tmp_path / "fresh.bin"
    tmp = tmp_path / "fresh.bin.tmp"
    tmp.write_bytes(b"data")

    replace_atomic(tmp, dst)

    assert dst.read_bytes() == b"data"


def test_clear_readonly_is_noop_on_missing_path(tmp_path: Path) -> None:
    clear_readonly(tmp_path / "does-not-exist.bin")  # must not raise


def test_clear_readonly_makes_file_writable(tmp_path: Path) -> None:
    target = tmp_path / "ro.bin"
    target.write_bytes(b"x")
    os.chmod(target, stat.S_IREAD)

    clear_readonly(target)

    target.write_bytes(b"y")  # must not raise
    assert target.read_bytes() == b"y"
