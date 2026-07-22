"""Unit tests for the fman-style favorites file loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.favorites import FavoriteDir, load_favorites


def test_load_parses_name_path_lines(tmp_path: Path) -> None:
    file = tmp_path / ".favoritedirs"
    file.write_text("Docs|D:\\some\\docs\nWork Stuff|\\\\server\\share\\work\n", encoding="utf-8")

    assert load_favorites(file) == [
        FavoriteDir(name="Docs", path=Path("D:/some/docs")),
        FavoriteDir(name="Work Stuff", path=Path("//server/share/work")),
    ]


def test_load_expands_home_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    file = tmp_path / ".favoritedirs"
    file.write_text("Downloads|~/Downloads\\Telegram\n", encoding="utf-8")

    assert load_favorites(file) == [
        FavoriteDir(name="Downloads", path=tmp_path / "Downloads" / "Telegram")
    ]


def test_load_skips_placeholder_blank_and_malformed_lines(tmp_path: Path) -> None:
    file = tmp_path / ".favoritedirs"
    file.write_text(
        "Angebote|{{Sync}}/GmbH\\Angebote\n"
        "\n"
        "no separator here\n"
        "|D:\\path-without-name\n"
        "Name without path|\n"
        "Kept|D:\\kept\n",
        encoding="utf-8",
    )

    assert load_favorites(file) == [FavoriteDir(name="Kept", path=Path("D:/kept"))]


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_favorites(tmp_path / "nope") == []
