"""Integration tests for the delete-page CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli import delete_page as delete_cli
from tests.conftest import MakePdf, PageSizesOf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def test_delete_page_cli_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="d.pdf")
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-delete-page", "2", str(source)])
    exit_code = delete_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(10, 10), (30, 30)]
    assert len(list(backup_dir.glob("*-d.pdf"))) == 1


def test_delete_page_cli_out_of_range(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="d.pdf")
    original_bytes = source.read_bytes()
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-delete-page", "5", str(source)])
    exit_code = delete_cli.main()

    assert exit_code != 0
    assert source.read_bytes() == original_bytes


def test_delete_page_cli_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_backup_dir(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.argv", ["pdf-delete-page", "1", str(tmp_path / "nope.pdf")])

    exit_code = delete_cli.main()

    assert exit_code != 0
