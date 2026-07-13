"""Unit tests for per-page link extraction and hint-label assignment."""

from __future__ import annotations

from pathlib import Path

import fitz

from app.gui.link_hint_controller import hint_labels
from app.pdf.links import LinkBox, page_links


def _pdf_with_links(tmp_path: Path) -> Path:
    target = tmp_path / "links.pdf"
    doc = fitz.open()
    try:
        page = doc.new_page()
        page.insert_link(
            {
                "kind": fitz.LINK_URI,
                "from": fitz.Rect(50, 60, 200, 75),
                "uri": "https://example.com/",
            }
        )
        page.insert_text((50, 120), "see https://printed.example/path here", fontsize=12)
        doc.save(str(target))
    finally:
        doc.close()
    return target


def test_extracts_annotation_link(tmp_path: Path) -> None:
    uris = [link.uri for link in page_links(_pdf_with_links(tmp_path), 0)]
    assert "https://example.com/" in uris


def test_extracts_bare_text_url(tmp_path: Path) -> None:
    links = page_links(_pdf_with_links(tmp_path), 0)
    assert any(link.uri == "https://printed.example/path" for link in links)


def test_links_are_typed_and_in_bounds(tmp_path: Path) -> None:
    links = page_links(_pdf_with_links(tmp_path), 0)
    assert links and all(isinstance(link, LinkBox) for link in links)
    for link in links:
        assert link.x0 < link.x1
        assert link.y0 < link.y1


def test_no_links_returns_empty(tmp_path: Path) -> None:
    target = tmp_path / "plain.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 80), "no urls here")
    doc.save(str(target))
    doc.close()
    assert page_links(target, 0) == []


def test_dedup_text_url_matching_annotation(tmp_path: Path) -> None:
    """A printed URL that is also a hyperlink annotation yields a single entry."""
    target = tmp_path / "dup.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 80), "https://dup.example/", fontsize=12)
    page.insert_link(
        {"kind": fitz.LINK_URI, "from": fitz.Rect(50, 68, 200, 84), "uri": "https://dup.example/"}
    )
    doc.save(str(target))
    doc.close()
    uris = [link.uri for link in page_links(target, 0)]
    assert uris.count("https://dup.example/") == 1


def test_trailing_punctuation_stripped(tmp_path: Path) -> None:
    target = tmp_path / "punct.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 80), "go to https://trail.example/end.", fontsize=12)
    doc.save(str(target))
    doc.close()
    uris = [link.uri for link in page_links(target, 0)]
    assert "https://trail.example/end" in uris


def test_hint_labels_single_letters() -> None:
    assert hint_labels(3) == ["a", "b", "c"]


def test_hint_labels_two_char_when_over_26() -> None:
    labels = hint_labels(30)
    assert len(labels) == 30
    assert len(set(labels)) == 30  # unique
    assert {len(label) for label in labels} == {2}  # all equal length


def test_hint_labels_zero() -> None:
    assert hint_labels(0) == []
