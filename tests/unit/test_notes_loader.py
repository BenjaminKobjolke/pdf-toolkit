"""Unit tests for release-notes loading and ordering."""

from __future__ import annotations

import json
from pathlib import Path

from app.release import schema
from app.release.notes_loader import ReleaseNote, load_release_notes


def _write_release(
    root: Path, version: str, build: int, *, locale: str = "en", **fields: object
) -> Path:
    folder = root / schema.FOLDER_NAME_FMT.format(version=version, build=build)
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        schema.KEY_VERSION: version,
        schema.KEY_BUILD: build,
        schema.KEY_DATE: "2026-01-01",
        schema.KEY_TITLE: f"Release {version}_{build}",
        schema.KEY_NOTES: ["change a", "change b"],
    }
    payload.update(fields)
    target = folder / schema.LOCALE_FILE_FMT.format(locale=locale)
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def test_missing_root_returns_empty(tmp_path: Path) -> None:
    assert load_release_notes(root=tmp_path / "absent") == []


def test_empty_root_returns_empty(tmp_path: Path) -> None:
    assert load_release_notes(root=tmp_path) == []


def test_parses_note_fields(tmp_path: Path) -> None:
    _write_release(tmp_path, "0.1.0", 3)
    notes = load_release_notes(root=tmp_path)
    assert len(notes) == 1
    note = notes[0]
    assert isinstance(note, ReleaseNote)
    assert note.version == "0.1.0"
    assert note.build == 3
    assert note.label == "0.1.0_3"
    assert note.notes == ("change a", "change b")


def test_sorted_newest_first(tmp_path: Path) -> None:
    _write_release(tmp_path, "0.1.0", 2)
    _write_release(tmp_path, "0.2.0", 1)
    _write_release(tmp_path, "0.1.0", 10)
    labels = [note.label for note in load_release_notes(root=tmp_path)]
    assert labels == ["0.2.0_1", "0.1.0_10", "0.1.0_2"]


def test_locale_falls_back_to_english(tmp_path: Path) -> None:
    _write_release(tmp_path, "0.1.0", 1, locale="en", title="English title")
    notes = load_release_notes(locale="de", root=tmp_path)
    assert notes[0].title == "English title"


def test_locale_prefers_requested(tmp_path: Path) -> None:
    _write_release(tmp_path, "0.1.0", 1, locale="en", title="English")
    _write_release(tmp_path, "0.1.0", 1, locale="de", title="Deutsch")
    notes = load_release_notes(locale="de", root=tmp_path)
    assert notes[0].title == "Deutsch"


def test_ignores_malformed_folders(tmp_path: Path) -> None:
    (tmp_path / "not-a-release").mkdir()
    (tmp_path / "0.1.0_x").mkdir()
    _write_release(tmp_path, "0.1.0", 1)
    notes = load_release_notes(root=tmp_path)
    assert [note.label for note in notes] == ["0.1.0_1"]


def test_ignores_release_without_json(tmp_path: Path) -> None:
    (tmp_path / "0.1.0_5").mkdir()
    assert load_release_notes(root=tmp_path) == []
