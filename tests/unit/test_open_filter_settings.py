"""Unit tests for the open-dialog filter store and extension parsing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.config.open_filter_settings import (
    DEFAULT_EXTENSIONS,
    OpenFilterSettings,
    OpenFilterSettingsStore,
    parse_extensions,
)
from tests.conftest import gui_backend


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("pdf, txt", (".pdf", ".txt")),
        ("PDF, Txt", (".pdf", ".txt")),
        (".md,.ini", (".md", ".ini")),
        ("pdf  txt,,  md", (".pdf", ".txt", ".md")),
        ("pdf, pdf, .PDF", (".pdf",)),
        ("", ()),
        (" ,  , ", ()),
    ],
)
def test_parse_extensions(text: str, expected: tuple[str, ...]) -> None:
    assert parse_extensions(text) == expected


def test_defaults_match_viewer_formats() -> None:
    assert OpenFilterSettings().extensions == DEFAULT_EXTENSIONS
    assert ".pdf" in DEFAULT_EXTENSIONS
    assert OpenFilterSettings().all_files is False


def test_defaults_when_absent(tmp_path: Path) -> None:
    store = OpenFilterSettingsStore(gui_backend(tmp_path))
    assert store.load() == OpenFilterSettings()


def test_round_trip_all_fields(tmp_path: Path) -> None:
    store = OpenFilterSettingsStore(gui_backend(tmp_path))
    saved = OpenFilterSettings(all_files=True, extensions=(".pdf", ".ini"))
    store.save(saved)
    assert store.load() == saved


def test_store_has_label(tmp_path: Path) -> None:
    assert OpenFilterSettingsStore(gui_backend(tmp_path)).label


def test_current_filter_both_modes() -> None:
    from PySide6.QtWidgets import QWidget

    from app.gui.open_filter_controller import OpenFilterController

    store = MagicMock(spec=OpenFilterSettingsStore)
    store.load.return_value = OpenFilterSettings(all_files=False, extensions=(".ini",))
    controller = OpenFilterController(MagicMock(spec=QWidget), store)
    assert controller.current_filter().patterns == (".ini",)

    store.load.return_value = OpenFilterSettings(all_files=True)
    controller = OpenFilterController(MagicMock(spec=QWidget), store)
    assert controller.current_filter().patterns == ()
