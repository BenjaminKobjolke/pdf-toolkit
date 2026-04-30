"""Integration tests for the pdft wizard CLI entry point."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.cli import pdft as pdft_cli
from tests.conftest import MakePdf, PageSizesOf


def _isolate_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    backup_dir = tmp_path / "backup"
    monkeypatch.setenv("PDF_TOOLKIT_BACKUP_DIR", str(backup_dir))
    return backup_dir


def _scripted(answers: list[str]) -> Iterator[str]:
    yield from answers


def _wire_prompts(
    monkeypatch: pytest.MonkeyPatch,
    *,
    inputs: list[str],
    pdf_paths: list[str],
) -> None:
    """Route ``input()`` to ``inputs`` queue and ``pt_prompt`` to ``pdf_paths`` queue."""
    input_iter = _scripted(inputs)
    path_iter = _scripted(pdf_paths)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_iter))
    monkeypatch.setattr("app.cli.pdft.pt_prompt", lambda *_a, **_kw: next(path_iter))
    monkeypatch.setattr("sys.argv", ["pdft"])


def test_pdft_swap_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="w.pdf")
    backup_dir = _isolate_backup_dir(monkeypatch, tmp_path)

    _wire_prompts(monkeypatch, inputs=["1"], pdf_paths=[str(source)])

    exit_code = pdft_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(20, 20), (10, 10)]
    assert len(list(backup_dir.glob("*-w.pdf"))) == 1


def test_pdft_delete_single_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="w.pdf")
    _isolate_backup_dir(monkeypatch, tmp_path)

    _wire_prompts(monkeypatch, inputs=["2", "2"], pdf_paths=[str(source)])

    exit_code = pdft_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(10, 10), (30, 30)]


def test_pdft_delete_range_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30), (40, 40), (50, 50)], name="w.pdf")
    _isolate_backup_dir(monkeypatch, tmp_path)

    _wire_prompts(monkeypatch, inputs=["3", "2", "3"], pdf_paths=[str(source)])

    exit_code = pdft_cli.main()

    assert exit_code == 0
    assert page_sizes_of(source) == [(10, 10), (40, 40), (50, 50)]


def test_pdft_quit_returns_zero_without_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="w.pdf")
    original_bytes = source.read_bytes()
    _isolate_backup_dir(monkeypatch, tmp_path)

    _wire_prompts(monkeypatch, inputs=["q"], pdf_paths=[])

    exit_code = pdft_cli.main()

    assert exit_code == 0
    assert source.read_bytes() == original_bytes
    assert page_sizes_of(source) == [(10, 10), (20, 20)]


def test_pdft_validation_error_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="w.pdf")
    original_bytes = source.read_bytes()
    _isolate_backup_dir(monkeypatch, tmp_path)

    _wire_prompts(monkeypatch, inputs=["1"], pdf_paths=[str(source)])

    exit_code = pdft_cli.main()

    assert exit_code != 0
    assert source.read_bytes() == original_bytes
