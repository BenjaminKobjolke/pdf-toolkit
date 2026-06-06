"""Unit tests for app.cli._common.run_to_new_file (no-backup runner)."""

from __future__ import annotations

from pathlib import Path

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, run_to_new_file
from app.config.settings import Settings
from tests.conftest import MakePdf


def _settings(tmp_path: Path) -> Settings:
    return Settings(backup_dir=tmp_path / "backup", log_level="INFO")


def test_run_to_new_file_runs_op_without_backup(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10)], name="doc.pdf")
    settings = _settings(tmp_path)
    called: list[Path] = []

    code = run_to_new_file(source, lambda p: called.append(p), settings)

    assert code == EXIT_OK
    assert called == [source]
    assert not settings.backup_dir.exists() or not list(settings.backup_dir.iterdir())


def test_run_to_new_file_missing_source_returns_usage(tmp_path: Path) -> None:
    def op_should_not_run(_p: Path) -> None:
        raise AssertionError("op should not run")

    code = run_to_new_file(tmp_path / "nope.pdf", op_should_not_run, _settings(tmp_path))

    assert code == EXIT_USAGE


def test_run_to_new_file_op_valueerror_returns_failure(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10)], name="doc.pdf")

    def op(_p: Path) -> None:
        raise ValueError("bad page")

    code = run_to_new_file(source, op, _settings(tmp_path))

    assert code == EXIT_FAILURE
