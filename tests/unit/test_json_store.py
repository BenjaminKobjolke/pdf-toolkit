"""Unit tests for the shared atomic JSON writer."""

from __future__ import annotations

import json
from pathlib import Path

from app.io.json_store import write_json_atomic


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
