"""Integration tests for the merge-folder CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from app.cli import merge_folder as merge_cli
from app.pdf.merger import MERGED_FILENAME
from tests.conftest import MakeImage, MakePdf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def test_merge_folder_cli_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    make_image: MakeImage,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    make_pdf([(100, 200)], name="a.pdf").rename(folder / "a.pdf")
    make_pdf([(300, 400), (500, 600)], name="b.pdf").rename(folder / "b.pdf")
    make_image("png", name="c.png").rename(folder / "c.png")
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-merge-folder", str(folder)])
    exit_code = merge_cli.main()

    assert exit_code == 0
    merged = folder / MERGED_FILENAME
    assert merged.is_file()
    reader = PdfReader(str(merged))
    assert len(reader.pages) == 4


def test_merge_folder_cli_backup_overwrite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    make_pdf([(100, 200)], name="a.pdf").rename(folder / "a.pdf")
    make_pdf([(999, 999)], name="staged.pdf").rename(folder / MERGED_FILENAME)
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-merge-folder", str(folder)])
    exit_code = merge_cli.main()

    assert exit_code == 0
    backups = list(backup_dir.glob("*-merged.pdf"))
    assert len(backups) == 1
    reader = PdfReader(str(folder / MERGED_FILENAME))
    assert len(reader.pages) == 1
    assert (float(reader.pages[0].mediabox.width), float(reader.pages[0].mediabox.height)) == (
        100.0,
        200.0,
    )


def test_merge_folder_cli_empty_folder_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    folder = tmp_path / "empty"
    folder.mkdir()
    _isolate_backup_dir(monkeypatch, tmp_path)

    monkeypatch.setattr("sys.argv", ["pdf-merge-folder", str(folder)])
    exit_code = merge_cli.main()

    assert exit_code != 0
    assert not (folder / MERGED_FILENAME).exists()


def test_merge_folder_cli_missing_folder_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_backup_dir(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.argv", ["pdf-merge-folder", str(tmp_path / "nope")])

    exit_code = merge_cli.main()

    assert exit_code != 0
