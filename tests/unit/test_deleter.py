"""Unit tests for app.pdf.deleter."""

from __future__ import annotations

import pytest

from app.pdf.deleter import delete_page, delete_page_range
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


def test_delete_range_middle(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30), (40, 40), (50, 50)])

    delete_page_range(source, start_page=2, end_page=3)

    assert page_sizes_of(source) == [(10, 10), (40, 40), (50, 50)]


def test_delete_range_single_page_equals_delete_page(
    make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])

    delete_page_range(source, start_page=2, end_page=2)

    assert page_sizes_of(source) == [(10, 10), (30, 30)]


def test_delete_range_first_to_n(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30), (40, 40)])

    delete_page_range(source, start_page=1, end_page=2)

    assert page_sizes_of(source) == [(30, 30), (40, 40)]


def test_delete_range_rejects_start_below_one(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="1-based"):
        delete_page_range(source, start_page=0, end_page=2)

    assert source.read_bytes() == original_bytes


def test_delete_range_rejects_end_before_start(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match=">= start"):
        delete_page_range(source, start_page=3, end_page=2)

    assert source.read_bytes() == original_bytes


def test_delete_range_rejects_end_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        delete_page_range(source, start_page=2, end_page=5)

    assert source.read_bytes() == original_bytes


def test_delete_range_refuses_full_pdf(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="empty"):
        delete_page_range(source, start_page=1, end_page=3)

    assert source.read_bytes() == original_bytes
