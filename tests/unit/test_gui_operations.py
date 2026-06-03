"""Unit tests for app.gui.operations.GuiOperationRunner (no Qt needed)."""

from __future__ import annotations

from pathlib import Path

from app.config.settings import Settings
from app.gui.operations import GuiOperationRunner
from app.pdf.deleter import delete_page
from app.pdf.merger import MERGED_FILENAME, merge_folder
from app.pdf.swapper import swap_two_pages
from tests.conftest import MakeImage, MakePdf, PageSizesOf


def _runner(tmp_path: Path) -> tuple[GuiOperationRunner, Path]:
    backup_dir = tmp_path / "backup"
    settings = Settings(backup_dir=backup_dir, log_level="INFO")
    return GuiOperationRunner(settings), backup_dir


def test_run_on_file_deletes_page_and_backs_up(
    tmp_path: Path, make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)], name="doc.pdf")
    runner, backup_dir = _runner(tmp_path)

    result = runner.run_on_file(pdf, lambda p: delete_page(p, 1))

    assert result.ok
    assert page_sizes_of(pdf) == [(300, 400)]
    assert len(list(backup_dir.glob("*-doc.pdf"))) == 1


def test_run_on_file_reports_core_error_message(
    tmp_path: Path, make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    runner, backup_dir = _runner(tmp_path)
    before = page_sizes_of(pdf)

    result = runner.run_on_file(pdf, swap_two_pages)

    assert not result.ok
    assert result.message  # carries the core ValueError text
    assert page_sizes_of(pdf) == before  # unchanged
    assert len(list(backup_dir.iterdir())) == 1  # backup still made


def test_run_on_file_missing_file(tmp_path: Path) -> None:
    runner, _ = _runner(tmp_path)

    result = runner.run_on_file(tmp_path / "nope.pdf", swap_two_pages)

    assert not result.ok
    assert "not found" in result.message


def test_run_folder_merge_writes_merged(tmp_path: Path, make_image: MakeImage) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    make_image("png", name="a.png")  # created in tmp_path
    (tmp_path / "a.png").replace(folder / "a.png")
    runner, _ = _runner(tmp_path)

    result = runner.run_folder_merge(folder, merge_folder)

    assert result.ok
    assert (folder / MERGED_FILENAME).is_file()
