"""Unit tests for app.cli._common.run_folder_merge."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, run_folder_merge
from app.config.settings import Settings
from app.pdf.merger import MERGED_FILENAME
from tests.conftest import MakePdf


def _settings(tmp_path: Path) -> Settings:
    return Settings(backup_dir=tmp_path / "backup", log_level="INFO")


def test_run_folder_merge_missing_folder_returns_usage(tmp_path: Path) -> None:
    def op_should_not_run(_folder: Path) -> None:
        raise AssertionError("op should not run")

    code = run_folder_merge(tmp_path / "nope", op_should_not_run, _settings(tmp_path))

    assert code == EXIT_USAGE


def test_run_folder_merge_backups_existing_output(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    pre = make_pdf([(10, 10)], name="staged.pdf")
    pre.rename(folder / MERGED_FILENAME)

    settings = _settings(tmp_path)
    called: list[Path] = []

    def op(folder_arg: Path) -> None:
        called.append(folder_arg)

    code = run_folder_merge(folder, op, settings)

    assert code == EXIT_OK
    assert called == [folder]
    backups = list(settings.backup_dir.glob("*-merged.pdf"))
    assert len(backups) == 1


def test_run_folder_merge_skips_backup_when_no_existing_output(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()

    settings = _settings(tmp_path)

    def op(_folder: Path) -> None:
        return None

    code = run_folder_merge(folder, op, settings)

    assert code == EXIT_OK
    assert not settings.backup_dir.exists() or not list(settings.backup_dir.iterdir())


def test_run_folder_merge_op_valueerror_returns_failure(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()

    def op(_folder: Path) -> None:
        raise ValueError("nothing supported")

    code = run_folder_merge(folder, op, _settings(tmp_path))

    assert code == EXIT_FAILURE


def test_run_folder_merge_op_oserror_returns_failure(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()

    def op(_folder: Path) -> None:
        raise OSError("disk full")

    code = run_folder_merge(folder, op, _settings(tmp_path))

    assert code == EXIT_FAILURE


def test_run_folder_merge_passes_through_exit_ok(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()

    code = run_folder_merge(folder, lambda _f: None, _settings(tmp_path))

    assert code == EXIT_OK


@pytest.mark.parametrize("name", ["MERGED.PDF", "Merged.Pdf", "merged.pdf"])
def test_run_folder_merge_backups_existing_output_case_insensitive(
    tmp_path: Path,
    make_pdf: MakePdf,
    name: str,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    pre = make_pdf([(10, 10)], name="staged.pdf")
    pre.rename(folder / name)

    settings = _settings(tmp_path)

    def op(_folder: Path) -> None:
        return None

    code = run_folder_merge(folder, op, settings)

    assert code == EXIT_OK
    backups = list(settings.backup_dir.glob(f"*-{name}"))
    assert len(backups) == 1
