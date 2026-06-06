"""Integration tests for the insert-page CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli import insert_page as insert_cli
from tests.conftest import MakeImage, MakePdf, PageSizesOf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def test_insert_pdf_cli_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-insert-page", str(insert), "1", str(source)])
    exit_code = insert_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(10, 10), (99, 99), (20, 20)]
    assert len(list(backup_dir.glob("*-doc.pdf"))) == 1


def test_insert_image_cli_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    make_image: MakeImage,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    image = make_image("png", name="pic.png")
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-insert-page", str(image), "2", str(source)])
    exit_code = insert_cli.main()

    assert exit_code == 0
    assert len(page_sizes_of(source)) == 3


def test_insert_cli_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    insert = make_pdf([(99, 99)], name="ins.pdf")
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr(
        "sys.argv", ["pdf-insert-page", str(insert), "1", str(tmp_path / "nope.pdf")]
    )
    exit_code = insert_cli.main()

    assert exit_code != 0
