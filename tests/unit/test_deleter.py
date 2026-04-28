"""Unit tests for app.pdf.deleter."""

from __future__ import annotations

import pytest

from app.pdf.deleter import delete_page
from tests.conftest import MakePdf, PageSizesOf


def test_delete_middle_page(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(100, 200), (300, 400), (500, 600)])

    delete_page(source, page_number=2)

    assert page_sizes_of(source) == [(100, 200), (500, 600)]


def test_delete_first_page(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(100, 200), (300, 400), (500, 600)])

    delete_page(source, page_number=1)

    assert page_sizes_of(source) == [(300, 400), (500, 600)]


def test_delete_last_page(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(100, 200), (300, 400), (500, 600)])

    delete_page(source, page_number=3)

    assert page_sizes_of(source) == [(100, 200), (300, 400)]


def test_delete_rejects_zero(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="1-based"):
        delete_page(source, page_number=0)

    assert source.read_bytes() == original_bytes


def test_delete_rejects_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        delete_page(source, page_number=3)

    assert source.read_bytes() == original_bytes


def test_delete_refuses_when_only_one_page(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="empty"):
        delete_page(source, page_number=1)

    assert source.read_bytes() == original_bytes
