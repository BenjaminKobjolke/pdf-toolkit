"""Integration tests for the delete-pages (range) CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli import delete_pages as delete_pages_cli
from tests.conftest import MakePdf, PageSizesOf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def test_delete_pages_cli_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30), (40, 40), (50, 50)], name="dr.pdf")
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-delete-pages", "2", "3", str(source)])
    exit_code = delete_pages_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(10, 10), (40, 40), (50, 50)]
    assert len(list(backup_dir.glob("*-dr.pdf"))) == 1


def test_delete_pages_cli_out_of_range(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="dr.pdf")
    original_bytes = source.read_bytes()
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-delete-pages", "2", "9", str(source)])
    exit_code = delete_pages_cli.main()

    assert exit_code != 0
    assert source.read_bytes() == original_bytes


def test_delete_pages_cli_reversed_range(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="dr.pdf")
    original_bytes = source.read_bytes()
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-delete-pages", "3", "2", str(source)])
    exit_code = delete_pages_cli.main()

    assert exit_code != 0
    assert source.read_bytes() == original_bytes


def test_delete_pages_cli_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_backup_dir(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.argv", ["pdf-delete-pages", "1", "2", str(tmp_path / "nope.pdf")])

    exit_code = delete_pages_cli.main()

    assert exit_code != 0
