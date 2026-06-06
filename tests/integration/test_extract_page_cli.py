"""Integration tests for the extract-page CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli import extract_page as extract_cli
from tests.conftest import MakePdf, PageSizesOf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def test_extract_cli_default_dest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    before = source.read_bytes()
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-extract-page", "2", str(source)])
    exit_code = extract_cli.main()

    assert exit_code == 0
    dest = source.with_name("doc-p02.pdf")
    assert page_sizes_of(dest) == [(20, 20)]
    # Original untouched; no backup made.
    assert source.read_bytes() == before
    assert not backup_dir.exists() or not list(backup_dir.iterdir())


def test_extract_cli_explicit_out(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    out = tmp_path / "picked.pdf"
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-extract-page", "3", str(source), "-o", str(out)])
    exit_code = extract_cli.main()

    assert exit_code == 0
    assert page_sizes_of(out) == [(30, 30)]


def test_extract_cli_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_backup_dir(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.argv", ["pdf-extract-page", "1", str(tmp_path / "nope.pdf")])

    exit_code = extract_cli.main()

    assert exit_code != 0
