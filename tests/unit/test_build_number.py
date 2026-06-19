"""Unit tests for the build-number reader/writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.release import build_number


def test_read_returns_default_when_missing(tmp_path: Path) -> None:
    assert build_number.read_build(tmp_path / "absent.txt") == 0


def test_write_then_read_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "build_version.txt"
    build_number.write_build(7, target)
    assert build_number.read_build(target) == 7


def test_read_falls_back_on_garbage(tmp_path: Path) -> None:
    target = tmp_path / "build_version.txt"
    target.write_text("not-a-number", encoding="utf-8")
    assert build_number.read_build(target) == 0


def test_increment_raises_value_and_persists(tmp_path: Path) -> None:
    target = tmp_path / "build_version.txt"
    build_number.write_build(4, target)
    assert build_number.increment(target) == 5
    assert build_number.read_build(target) == 5


def test_decrement_floors_at_zero(tmp_path: Path) -> None:
    target = tmp_path / "build_version.txt"
    build_number.write_build(0, target)
    assert build_number.decrement(target) == 0


def test_write_rejects_negative(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_number.write_build(-1, tmp_path / "build_version.txt")


def test_main_get_prints_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "build_version.txt"
    build_number.write_build(9, target)
    monkeypatch.setattr(build_number, "build_file", lambda: target)
    assert build_number.main(["get"]) == 0
    assert capsys.readouterr().out.strip() == "9"


def test_main_unknown_action_returns_2() -> None:
    assert build_number.main(["bogus"]) == 2
