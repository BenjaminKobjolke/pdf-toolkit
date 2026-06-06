"""Unit tests for renaming a PDF and its sidecar together."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.pdf.image_spec import SidecarDocument
from app.pdf.renamer import rename_document
from app.pdf.sidecar import save_sidecar, sidecar_path
from tests.conftest import MakePdf


def test_renames_pdf(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)], name="old.pdf")
    target = pdf.with_name("new.pdf")
    rename_document(pdf, target)
    assert target.is_file()
    assert not pdf.exists()


def test_renames_sidecar_alongside(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)], name="old.pdf")
    save_sidecar(pdf, SidecarDocument(fields=()))
    target = pdf.with_name("new.pdf")
    rename_document(pdf, target)
    assert sidecar_path(target).is_file()
    assert not sidecar_path(pdf).exists()


def test_missing_sidecar_is_fine(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)], name="old.pdf")
    target = pdf.with_name("new.pdf")
    rename_document(pdf, target)  # no sidecar present
    assert target.is_file()


def test_target_exists_raises(make_pdf: MakePdf, tmp_path: Path) -> None:
    pdf = make_pdf([(100, 200)], name="old.pdf")
    existing = make_pdf([(50, 50)], name="taken.pdf")
    with pytest.raises(ValueError):
        rename_document(pdf, existing)
    assert pdf.is_file()  # original untouched
