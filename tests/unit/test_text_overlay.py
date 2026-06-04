"""Unit tests for coordinate math and the fitz text-overlay export."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import fitz
import pytest

from app.pdf.text_overlay import (
    apply_text_overlay,
    embedded_output_path,
    scene_to_pdf_rect,
    screen_px_to_point_size,
)
from app.pdf.text_spec import TextFieldSpec

POINTS_PER_PX = 1.0 / 1.5


def _field(**overrides: object) -> TextFieldSpec:
    base: dict[str, object] = {
        "page_index": 0,
        "x": 150.0,
        "y": 75.0,
        "width": 300.0,
        "height": 30.0,
        "text": "Hello",
        "font_family": "Helvetica",
        "font_size": 18.0,
        "color": "#ff0000",
        "bg_color": None,
        "bold": False,
        "italic": False,
    }
    base.update(overrides)
    return TextFieldSpec(**base)  # type: ignore[arg-type]


# --- pure coordinate math ---------------------------------------------------


def test_scene_to_pdf_rect_divides_by_zoom() -> None:
    assert scene_to_pdf_rect(150.0, 75.0, 300.0, 30.0, 1.5) == (100.0, 50.0, 300.0, 70.0)


def test_scene_to_pdf_rect_identity_at_zoom_one() -> None:
    assert scene_to_pdf_rect(10.0, 20.0, 5.0, 6.0, 1.0) == (10.0, 20.0, 15.0, 26.0)


def test_screen_px_to_point_size() -> None:
    assert screen_px_to_point_size(18.0, 1.5) == pytest.approx(12.0)


# --- fitz export ------------------------------------------------------------


def _make_pdf(path: Path, pages: int = 1) -> Path:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=595, height=842)  # A4 points
    doc.save(str(path))
    doc.close()
    return path


def test_apply_writes_text_at_expected_position(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    apply_text_overlay(pdf, [_field(text="Marker")])

    doc = fitz.open(str(pdf))
    try:
        page = doc.load_page(0)
        assert "Marker" in page.get_text("text")
        words = page.get_text("words")
        assert words, "expected at least one word"
        x0, y0 = words[0][0], words[0][1]
        assert x0 == pytest.approx(150.0 * POINTS_PER_PX, abs=3.0)
        assert y0 == pytest.approx(75.0 * POINTS_PER_PX, abs=4.0)
    finally:
        doc.close()


def test_short_text_stays_on_one_line(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    apply_text_overlay(pdf, [_field(text="Text", width=40.0)])

    doc = fitz.open(str(pdf))
    try:
        words = doc.load_page(0).get_text("words")
        # All glyphs land on a single baseline -> one word, not split across rows.
        assert len(words) == 1
        assert words[0][4] == "Text"
    finally:
        doc.close()


def test_multi_line_text_keeps_its_breaks(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    apply_text_overlay(pdf, [_field(text="Line1\nLine2")])

    doc = fitz.open(str(pdf))
    try:
        words = doc.load_page(0).get_text("words")
        rows = {round(w[1]) for w in words}  # distinct baseline tops
        assert len(rows) == 2
    finally:
        doc.close()


def test_apply_draws_background_rect_only_when_set(tmp_path: Path) -> None:
    with_bg = _make_pdf(tmp_path / "bg.pdf")
    apply_text_overlay(with_bg, [_field(bg_color="#ffff00")])
    no_bg = _make_pdf(tmp_path / "nobg.pdf")
    apply_text_overlay(no_bg, [_field(bg_color=None)])

    def fill_rects(path: Path) -> int:
        doc = fitz.open(str(path))
        try:
            return sum(1 for d in doc.load_page(0).get_drawings() if d.get("fill"))
        finally:
            doc.close()

    assert fill_rects(with_bg) >= 1
    assert fill_rects(no_bg) == 0


def test_apply_rejects_out_of_range_page(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf", pages=1)
    with pytest.raises(ValueError):
        apply_text_overlay(pdf, [_field(page_index=5)])


def test_apply_rejects_bad_hex(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    with pytest.raises(ValueError):
        apply_text_overlay(pdf, [_field(color="red")])


def test_apply_rejects_encrypted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    real_open = fitz.open

    def fake_open(*args: object, **kwargs: object) -> object:
        doc = real_open(*args, **kwargs)
        wrapper = MagicMock(wraps=doc)
        wrapper.is_encrypted = True
        return wrapper

    monkeypatch.setattr(fitz, "open", fake_open)
    with pytest.raises(ValueError):
        apply_text_overlay(pdf, [_field()])


def test_apply_leaves_no_tmp_file(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    apply_text_overlay(pdf, [_field()])
    assert list(tmp_path.glob("*.tmp")) == []


def test_apply_no_fields_is_noop(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    apply_text_overlay(pdf, [])
    assert pdf.is_file()


def test_embedded_output_path_inserts_suffix(tmp_path: Path) -> None:
    assert embedded_output_path(tmp_path / "doc.pdf") == tmp_path / "doc_text-embedded.pdf"


def test_apply_writes_to_output_leaving_source(tmp_path: Path) -> None:
    pdf = _make_pdf(tmp_path / "doc.pdf")
    out = tmp_path / "doc_text-embedded.pdf"
    apply_text_overlay(pdf, [_field(text="Copy")], out)

    assert out.is_file()
    doc = fitz.open(str(out))
    try:
        assert "Copy" in doc.load_page(0).get_text("text")
    finally:
        doc.close()
    src = fitz.open(str(pdf))
    try:
        assert "Copy" not in src.load_page(0).get_text("text")  # source untouched
    finally:
        src.close()
