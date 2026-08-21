"""Unit tests for the persisted OCR settings store."""

from __future__ import annotations

from pathlib import Path

from app.config.ocr_settings import OcrSettings, OcrSettingsStore
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> OcrSettingsStore:
    return OcrSettingsStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_defaults_when_absent(tmp_path: Path) -> None:
    assert _store(tmp_path).load() == OcrSettings(language="")


def test_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save(OcrSettings(language="de-DE"))
    assert store.load().language == "de-DE"


def test_label(tmp_path: Path) -> None:
    assert _store(tmp_path).label == "OCR language"
