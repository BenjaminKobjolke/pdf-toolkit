"""Unit tests for the shared atomic JSON writer."""

from __future__ import annotations

import json
from pathlib import Path

from app.io.json_store import read_versioned_dict, write_json_atomic, write_versioned


def test_write_then_read_round_trips(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    payload = {"version": 1, "items": [1, 2, 3]}
    write_json_atomic(target, payload)
    assert json.loads(target.read_text(encoding="utf-8")) == payload


def test_write_leaves_no_tmp_file(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    write_json_atomic(target, {"a": 1})
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_overwrites_existing(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    write_json_atomic(target, {"v": 1})
    write_json_atomic(target, {"v": 2})
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 2}


def test_write_versioned_injects_version_and_creates_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "data.json"
    write_versioned(target, 3, {"a": 1})
    assert json.loads(target.read_text(encoding="utf-8")) == {"version": 3, "a": 1}


def test_read_versioned_round_trips(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    write_versioned(target, 1, {"a": 1})
    assert read_versioned_dict(target, 1) == {"version": 1, "a": 1}


def test_read_versioned_missing_is_none(tmp_path: Path) -> None:
    assert read_versioned_dict(tmp_path / "missing.json", 1) is None


def test_read_versioned_corrupt_is_none(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    target.write_text("{ not json", encoding="utf-8")
    assert read_versioned_dict(target, 1) is None


def test_read_versioned_wrong_version_is_none(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    write_versioned(target, 1, {"a": 1})
    assert read_versioned_dict(target, 2) is None
