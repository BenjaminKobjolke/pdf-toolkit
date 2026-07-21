"""Unit tests for the name-filtering helpers of the file-browser model.

Split out of ``test_file_browser_model.py`` (at the file-length cap), grouped
by domain: everything about matching names against typed queries lives here.
"""

from __future__ import annotations

from pathlib import Path

from app.gui.file_browser_model import FsEntry, matches_all_terms, substring_filter


def test_substring_filter_is_case_insensitive() -> None:
    entries = [
        FsEntry("Report.pdf", Path("Report.pdf"), False),
        FsEntry("notes.txt", Path("notes.txt"), False),
    ]
    assert [e.name for e in substring_filter(entries, "REP")] == ["Report.pdf"]


def test_substring_filter_empty_keeps_all() -> None:
    entries = [FsEntry("a", Path("a"), False)]
    assert substring_filter(entries, "") == entries


def test_substring_filter_multi_term_uses_and_semantics() -> None:
    entries = [
        FsEntry("20260218_electronics.jpg", Path("20260218_electronics.jpg"), False),
        FsEntry("electronics.png", Path("electronics.png"), False),
    ]
    assert [e.name for e in substring_filter(entries, "elec jpg")] == ["20260218_electronics.jpg"]


def test_matches_all_terms_empty_query_matches_everything() -> None:
    assert matches_all_terms("anything.pdf", "")
    assert matches_all_terms("anything.pdf", "   ")


def test_matches_all_terms_multi_term_any_order() -> None:
    assert matches_all_terms("20260218_electronics.jpg", "elec jpg")
    assert matches_all_terms("20260218_electronics.jpg", "jpg elec")


def test_matches_all_terms_is_case_insensitive() -> None:
    assert matches_all_terms("Report.PDF", "report pdf")


def test_matches_all_terms_rejects_when_one_term_misses() -> None:
    assert not matches_all_terms("20260218_electronics.jpg", "elec png")
