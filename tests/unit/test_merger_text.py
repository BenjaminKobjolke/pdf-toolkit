"""Unit tests for app.pdf.merger text merging (txt / md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.pdf.merger import (
    find_existing_merged,
    merge_folder,
    merged_output_path,
    scan_folder,
)
from tests.conftest import MakePdf


def _move(target: Path, dest: Path) -> Path:
    target.rename(dest)
    return dest


def test_merged_output_path_pdf_folder(tmp_path: Path, make_pdf: MakePdf) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")
    assert merged_output_path(folder).name == "merged.pdf"


def test_merged_output_path_txt_and_md(tmp_path: Path) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "a.txt").write_text("x", encoding="utf-8")
    assert merged_output_path(folder).name == "merged.txt"

    md = tmp_path / "md"
    md.mkdir()
    (md / "a.md").write_text("x", encoding="utf-8")
    (md / "b.md").write_text("y", encoding="utf-8")
    assert merged_output_path(md).name == "merged.md"


def test_merged_output_path_mixed_text_extensions_defaults_to_txt(tmp_path: Path) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "a.txt").write_text("x", encoding="utf-8")
    (folder / "b.md").write_text("y", encoding="utf-8")
    assert merged_output_path(folder).name == "merged.txt"


def test_merged_output_path_mixed_text_and_pdf_raises(tmp_path: Path, make_pdf: MakePdf) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")
    (folder / "b.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot merge text and PDF"):
        merged_output_path(folder)


def test_merge_folder_concatenates_txt(tmp_path: Path) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "a.txt").write_text("alpha", encoding="utf-8")
    (folder / "b.txt").write_text("beta", encoding="utf-8")

    merge_folder(folder)

    merged = folder / "merged.txt"
    assert merged.is_file()
    assert merged.read_text(encoding="utf-8") == "alpha\n\nbeta"


def test_merge_folder_concatenates_md(tmp_path: Path) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "a.md").write_text("# A", encoding="utf-8")
    (folder / "b.md").write_text("# B", encoding="utf-8")

    merge_folder(folder)

    assert (folder / "merged.md").read_text(encoding="utf-8") == "# A\n\n# B"


def test_merge_folder_text_mixed_with_pdf_raises(tmp_path: Path, make_pdf: MakePdf) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")
    (folder / "b.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot merge text and PDF"):
        merge_folder(folder)


def test_find_existing_merged_finds_text_output(tmp_path: Path) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "merged.md").write_text("x", encoding="utf-8")
    found = find_existing_merged(folder)
    assert found is not None
    assert found.name == "merged.md"


def test_scan_folder_excludes_prior_text_output(tmp_path: Path) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "a.txt").write_text("x", encoding="utf-8")
    (folder / "merged.txt").write_text("stale", encoding="utf-8")
    names = [p.name for p in scan_folder(folder, (".txt", ".md"))]
    assert names == ["a.txt"]
