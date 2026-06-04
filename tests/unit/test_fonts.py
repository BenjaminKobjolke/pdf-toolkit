"""Unit tests for the font-family -> file resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.pdf import fonts
from app.pdf.fonts import FontRequest, resolve_font


@pytest.fixture
def fake_index(monkeypatch: pytest.MonkeyPatch) -> dict[tuple[str, bool, bool], Path]:
    index = {
        ("arial", False, False): Path("C:/Windows/Fonts/arial.ttf"),
        ("arial", True, False): Path("C:/Windows/Fonts/arialbd.ttf"),
    }
    monkeypatch.setattr(fonts, "_font_index", lambda: index)
    return index


def test_exact_match_returns_file(fake_index: dict[tuple[str, bool, bool], Path]) -> None:
    resolved = resolve_font(FontRequest("Arial", bold=False, italic=False))
    assert resolved.fontfile == Path("C:/Windows/Fonts/arial.ttf")
    assert resolved.fontname


def test_bold_match_returns_bold_file(fake_index: dict[tuple[str, bool, bool], Path]) -> None:
    resolved = resolve_font(FontRequest("Arial", bold=True, italic=False))
    assert resolved.fontfile == Path("C:/Windows/Fonts/arialbd.ttf")


def test_bold_without_bold_file_falls_back_to_builtin(
    fake_index: dict[tuple[str, bool, bool], Path],
) -> None:
    # Only regular + bold exist; italic bold should fall back to a Base14 builtin.
    resolved = resolve_font(FontRequest("Arial", bold=True, italic=True))
    assert resolved.fontfile is None
    assert resolved.fontname == fonts.BASE14_BOLD_ITALIC


def test_unknown_family_falls_back_to_builtin(
    fake_index: dict[tuple[str, bool, bool], Path],
) -> None:
    resolved = resolve_font(FontRequest("Nonexistent", bold=False, italic=False))
    assert resolved.fontfile is None
    assert resolved.fontname == fonts.BASE14_REGULAR


def test_resolve_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> dict[tuple[str, bool, bool], Path]:
        raise OSError("registry unavailable")

    monkeypatch.setattr(fonts, "_font_index", boom)
    resolved = resolve_font(FontRequest("Whatever", bold=True, italic=False))
    assert resolved.fontfile is None
    assert resolved.fontname == fonts.BASE14_BOLD
