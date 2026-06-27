"""Unit tests for per-page word-box extraction."""

from __future__ import annotations

from app.pdf.words import WordBox, page_text, page_words
from tests.conftest import MakeSearchablePdf


def test_returns_words_in_reading_order(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["the quick brown fox"])
    words = page_words(pdf, 0)
    assert [w.text for w in words] == ["the", "quick", "brown", "fox"]
    assert all(isinstance(w, WordBox) for w in words)
    assert [w.index for w in words] == [0, 1, 2, 3]


def test_boxes_are_sane(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["hello"])
    word = page_words(pdf, 0)[0]
    assert word.x0 < word.x1
    assert word.y0 < word.y1
    assert word.x0 >= 0
    assert word.y0 >= 0


def test_line_key_groups_same_line(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["one two three"])
    keys = {w.line_key for w in page_words(pdf, 0)}
    assert len(keys) == 1  # one inserted line -> one line key


def test_empty_page_returns_empty(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf([""])
    assert page_words(pdf, 0) == []


def test_reads_requested_page(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["first page", "second page"])
    assert [w.text for w in page_words(pdf, 1)] == ["second", "page"]


def test_page_text_returns_page_content(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["hello world", "second page"])
    assert page_text(pdf, 0).strip() == "hello world"
    assert page_text(pdf, 1).strip() == "second page"


def test_page_text_empty_for_blank_page(make_searchable_pdf: MakeSearchablePdf) -> None:
    assert page_text(make_searchable_pdf([""]), 0) == ""
