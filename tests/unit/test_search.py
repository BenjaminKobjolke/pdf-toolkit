"""Unit tests for full-text PDF search."""

from __future__ import annotations

from app.pdf.search import SearchHit, search_pdf
from tests.conftest import MakeSearchablePdf


def test_finds_match_on_each_page(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["Hello world", "Hello again", "nothing here"])
    hits = search_pdf(pdf, "Hello")
    pages = {hit.page_index for hit in hits}
    assert pages == {0, 1}
    assert all(isinstance(h, SearchHit) for h in hits)


def test_hits_are_ordered_by_page(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["alpha match", "beta", "alpha match"])
    hits = search_pdf(pdf, "alpha")
    assert [h.page_index for h in hits] == [0, 2]


def test_case_insensitive(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["LaLa Test"])
    assert search_pdf(pdf, "lala")


def test_rects_are_in_page_bounds(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["findme"])
    hit = search_pdf(pdf, "findme")[0]
    assert hit.x0 < hit.x1
    assert hit.y0 < hit.y1
    assert hit.x0 >= 0
    assert hit.y0 >= 0


def test_snippet_contains_query(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["the quick brown fox"])
    hit = search_pdf(pdf, "quick")[0]
    assert "quick" in hit.snippet.lower()


def test_empty_query_returns_empty(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["whatever"])
    assert search_pdf(pdf, "") == []
    assert search_pdf(pdf, "   ") == []


def test_no_match_returns_empty(make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["abc"])
    assert search_pdf(pdf, "zzz") == []
