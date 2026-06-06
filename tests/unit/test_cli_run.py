"""Unit tests for the shared CLI runner and the rotate/move entry points."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

from app.cli import move_page as move_cli
from app.cli import rotate_page as rotate_cli
from app.cli._common import EXIT_OK, EXIT_USAGE, run_cli
from tests.conftest import MakePdf, PageSizesOf


def test_run_cli_runs_op_on_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "target"])
    seen: dict[str, Path] = {}

    def parse(argv: list[str]) -> argparse.Namespace:
        ns = argparse.Namespace()
        ns.value = argv[0]
        return ns

    def op(a: argparse.Namespace) -> object:
        def _op(path: Path) -> None:
            seen["path"] = path

        return _op

    def runner(target: Path, op_fn: object, _settings: object) -> int:
        op_fn(target)  # type: ignore[operator]
        return EXIT_OK

    code = run_cli(parse, lambda a: Path(a.value), op, runner=runner)  # type: ignore[arg-type]

    assert code == EXIT_OK
    assert seen["path"] == Path("target")


def _no_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog"])


def test_run_cli_maps_int_systemexit_to_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_argv(monkeypatch)

    def parse(_argv: list[str]) -> argparse.Namespace:
        raise SystemExit(2)

    code = run_cli(parse, lambda a: Path("x"), lambda a: lambda p: None)

    assert code == 2


def test_run_cli_maps_non_int_systemexit_to_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_argv(monkeypatch)

    def parse(_argv: list[str]) -> argparse.Namespace:
        raise SystemExit("bad usage")

    code = run_cli(parse, lambda a: Path("x"), lambda a: lambda p: None)

    assert code == EXIT_USAGE


def test_rotate_page_cli_rotates_and_backs_up(
    tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(tmp_path / "backup"))
    monkeypatch.setattr(sys, "argv", ["pdf-rotate-page", "1", "90", str(pdf)])

    assert rotate_cli.main() == EXIT_OK
    assert [page.rotation for page in PdfReader(str(pdf)).pages] == [90, 0]
    assert len(list((tmp_path / "backup").glob("*.pdf"))) == 1


def test_rotate_page_cli_rejects_bad_degrees(
    tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = make_pdf([(100, 200)])
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(tmp_path / "backup"))
    monkeypatch.setattr(sys, "argv", ["pdf-rotate-page", "1", "45", str(pdf)])

    assert rotate_cli.main() == EXIT_USAGE


def test_move_page_cli_reorders(
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = make_pdf([(10, 10), (20, 20), (30, 30)])
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(tmp_path / "backup"))
    monkeypatch.setattr(sys, "argv", ["pdf-move-page", "1", "3", str(pdf)])

    assert move_cli.main() == EXIT_OK
    assert page_sizes_of(pdf) == [(20, 20), (30, 30), (10, 10)]
    assert len(list((tmp_path / "backup").glob("*.pdf"))) == 1
