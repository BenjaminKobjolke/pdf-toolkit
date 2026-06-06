"""Unit tests for the image copy-vs-reference choice store."""

from __future__ import annotations

from pathlib import Path

from app.config.image_choice_settings import CHOICE_COPY, CHOICE_REFERENCE, ImageChoiceStore


def test_round_trip_and_reset(tmp_path: Path) -> None:
    store = ImageChoiceStore(tmp_path / "choice.json")
    assert store.load() is None
    store.save(CHOICE_COPY)
    assert store.load() == CHOICE_COPY
    store.save(CHOICE_REFERENCE)
    assert store.load() == CHOICE_REFERENCE
    store.reset()
    assert store.load() is None


def test_ignores_unknown_value(tmp_path: Path) -> None:
    store = ImageChoiceStore(tmp_path / "choice.json")
    store.save("bogus")
    assert store.load() is None


def test_label() -> None:
    assert "copy" in ImageChoiceStore(Path("x")).label.lower()
