"""Unit tests for ``save_copy`` — the Save-As file copy of the working PDF."""

from __future__ import annotations

from pathlib import Path

from app.gui.working_document import save_copy
from app.pdf.sidecar import sidecar_path


def test_copies_pdf_and_sidecar(tmp_path: Path) -> None:
    working = tmp_path / "working.pdf"
    working.write_bytes(b"%PDF-fake")
    sidecar_path(working).write_text("{}", encoding="utf-8")
    dest = tmp_path / "out" / "saved.pdf"
    dest.parent.mkdir()

    save_copy(working, dest)

    assert dest.read_bytes() == b"%PDF-fake"
    assert sidecar_path(dest).read_text(encoding="utf-8") == "{}"


def test_copies_pdf_only_when_no_sidecar(tmp_path: Path) -> None:
    working = tmp_path / "working.pdf"
    working.write_bytes(b"%PDF-fake")
    dest = tmp_path / "saved.pdf"

    save_copy(working, dest)

    assert dest.read_bytes() == b"%PDF-fake"
    assert not sidecar_path(dest).exists()
