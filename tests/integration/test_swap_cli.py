"""Integration tests for the swap CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli import swap as swap_cli
from tests.conftest import MakePdf, PageSizesOf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def test_swap_cli_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(100, 200), (300, 400)], name="doc.pdf")
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-swap", str(source)])
    exit_code = swap_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(300, 400), (100, 200)]
    backups = list(backup_dir.glob("*-doc.pdf"))
    assert len(backups) == 1


def test_swap_cli_rejects_three_pages(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    original_bytes = source.read_bytes()
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-swap", str(source)])
    exit_code = swap_cli.main()

    assert exit_code != 0
    assert source.read_bytes() == original_bytes
    # Backup is still created (per spec) even when validation fails.
    assert any(backup_dir.glob("*-doc.pdf"))


def test_swap_cli_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_backup_dir(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.argv", ["pdf-swap", str(tmp_path / "nope.pdf")])

    exit_code = swap_cli.main()

    assert exit_code != 0
