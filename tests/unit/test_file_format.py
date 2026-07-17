"""Unit tests for app.pdf.file_format."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.text_view_settings import TextViewSettings
from app.pdf.file_format import FileFormat, open_fitz, set_text_view_settings
from tests.conftest import MakePdf


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("a.pdf", FileFormat.PDF),
        ("a.PDF", FileFormat.PDF),
        ("a.txt", FileFormat.TXT),
        ("notes.md", FileFormat.MD),
        ("a.docx", None),
        ("a", None),
    ],
)
def test_of_maps_suffix(name: str, expected: FileFormat | None) -> None:
    assert FileFormat.of(Path(name)) == expected


def test_of_none_path() -> None:
    assert FileFormat.of(None) is None


def test_of_sniffs_unknown_suffix_text_as_txt(tmp_path: Path) -> None:
    ini = tmp_path / "config.ini"
    ini.write_text("[section]\nkey = value\n", encoding="utf-8")
    assert FileFormat.of(ini) is FileFormat.TXT


def test_of_rejects_binary_content(tmp_path: Path) -> None:
    blob = tmp_path / "data.bin"
    blob.write_bytes(b"MZ\x00\x01\x02binary\x00stuff")
    assert FileFormat.of(blob) is None


def test_of_rejects_non_utf8_content(tmp_path: Path) -> None:
    blob = tmp_path / "legacy.dat"
    blob.write_bytes(b"\xff\xfe\xfd totally not utf-8 \xff")
    assert FileFormat.of(blob) is None


def test_of_unknown_suffix_missing_file_is_none(tmp_path: Path) -> None:
    assert FileFormat.of(tmp_path / "ghost.ini") is None


def test_of_suffix_wins_over_content(tmp_path: Path) -> None:
    # A known suffix is trusted without sniffing — .pdf stays PDF even if the
    # bytes are plain text.
    fake = tmp_path / "fake.pdf"
    fake.write_text("just text\n", encoding="utf-8")
    assert FileFormat.of(fake) is FileFormat.PDF


def test_open_fitz_opens_sniffed_ini_as_text(tmp_path: Path) -> None:
    ini = tmp_path / "settings.ini"
    ini.write_text("[main]\nvalue = 1\n" * 20, encoding="utf-8")
    set_text_view_settings(TextViewSettings())
    doc = open_fitz(ini)
    try:
        assert doc.page_count >= 1
        assert "[main]" in doc.load_page(0).get_text()
    finally:
        doc.close()


def test_open_fitz_opens_md_where_bare_fitz_would_fail(tmp_path: Path) -> None:
    md = tmp_path / "note.md"
    md.write_text("# Heading\n\nsome text\n" * 20, encoding="utf-8")
    doc = open_fitz(md)
    try:
        assert doc.page_count >= 1
    finally:
        doc.close()


def test_open_fitz_renders_markdown_formatted(tmp_path: Path) -> None:
    # Markdown is rendered (## -> heading), not shown as raw source: the literal
    # "##" must not survive into the rendered page text.
    md = tmp_path / "note.md"
    md.write_text("## A Heading\n\nbody text\n", encoding="utf-8")
    set_text_view_settings(TextViewSettings())
    doc = open_fitz(md)
    try:
        text = doc.load_page(0).get_text()
        assert "A Heading" in text
        assert "##" not in text
    finally:
        doc.close()


def test_open_fitz_opens_txt(tmp_path: Path) -> None:
    txt = tmp_path / "note.txt"
    txt.write_text("hello world\n" * 40, encoding="utf-8")
    doc = open_fitz(txt)
    try:
        assert doc.page_count >= 1
    finally:
        doc.close()


def test_open_fitz_opens_pdf(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(200, 200)])
    doc = open_fitz(pdf)
    try:
        assert doc.page_count == 1
    finally:
        doc.close()
