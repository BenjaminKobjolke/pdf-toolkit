"""Unit tests for app.gui.working_document.WorkingDocument."""

from __future__ import annotations

import os
from pathlib import Path

from app.config.settings import Settings
from app.gui.working_document import WorkingDocument
from app.pdf.sidecar import sidecar_path
from app.pdf.swapper import swap_two_pages
from tests.conftest import MakePdf, PageSizesOf

_EMPTY_SIDECAR = '{"version": 1, "fields": []}'


def _settings(tmp_path: Path) -> Settings:
    return Settings(backup_dir=tmp_path / "backup", log_level="INFO")


def test_open_copies_pdf_and_seeds_sidecar(tmp_path: Path, make_pdf: MakePdf) -> None:
    original = make_pdf([(10, 10), (20, 20)])
    sidecar_path(original).write_text(_EMPTY_SIDECAR, encoding="utf-8")

    doc = WorkingDocument(_settings(tmp_path))
    working = doc.open(original)

    assert working != original
    assert working.is_file()
    assert sidecar_path(working).is_file()
    assert doc.original() == original
    assert doc.working() == working
    assert not doc.is_dirty()


def test_working_mutation_does_not_touch_original(
    tmp_path: Path, make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    original = make_pdf([(10, 10), (20, 20)])
    original_bytes = original.read_bytes()

    doc = WorkingDocument(_settings(tmp_path))
    working = doc.open(original)
    swap_two_pages(working)
    doc.mark_dirty()

    assert original.read_bytes() == original_bytes
    assert doc.is_dirty()
    assert page_sizes_of(working) == [(20, 20), (10, 10)]


def test_save_propagates_to_original_with_one_backup(
    tmp_path: Path, make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    original = make_pdf([(10, 10), (20, 20)])
    settings = _settings(tmp_path)

    doc = WorkingDocument(settings)
    working = doc.open(original)
    swap_two_pages(working)
    doc.mark_dirty()
    result = doc.save()

    assert result.ok
    assert page_sizes_of(original) == [(20, 20), (10, 10)]
    assert not doc.is_dirty()
    assert len(list(settings.backup_dir.glob("*.pdf"))) == 1


def test_save_propagates_working_sidecar(tmp_path: Path, make_pdf: MakePdf) -> None:
    original = make_pdf([(10, 10)])

    doc = WorkingDocument(_settings(tmp_path))
    working = doc.open(original)
    sidecar_path(working).write_text(_EMPTY_SIDECAR, encoding="utf-8")
    doc.mark_dirty()

    assert doc.save().ok
    assert sidecar_path(original).is_file()


def test_save_removes_stale_original_sidecar(tmp_path: Path, make_pdf: MakePdf) -> None:
    original = make_pdf([(10, 10)])
    sidecar_path(original).write_text(_EMPTY_SIDECAR, encoding="utf-8")

    doc = WorkingDocument(_settings(tmp_path))
    working = doc.open(original)
    os.remove(sidecar_path(working))  # user cleared every field
    doc.mark_dirty()

    assert doc.save().ok
    assert not sidecar_path(original).exists()


def test_close_deletes_working_files(tmp_path: Path, make_pdf: MakePdf) -> None:
    original = make_pdf([(10, 10)])
    sidecar_path(original).write_text(_EMPTY_SIDECAR, encoding="utf-8")

    doc = WorkingDocument(_settings(tmp_path))
    working = doc.open(original)
    assert working.is_file() and sidecar_path(working).is_file()

    doc.close()

    assert not working.exists()
    assert not sidecar_path(working).exists()
    assert doc.working() is None
    assert doc.original() is None


def test_save_without_open_document_fails(tmp_path: Path) -> None:
    doc = WorkingDocument(_settings(tmp_path))

    result = doc.save()

    assert not result.ok
