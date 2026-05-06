"""Unit tests for app.pdf.merger."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from pypdf import PdfReader

from app.pdf.merger import (
    MERGED_FILENAME,
    TMP_SUFFIX,
    merge_folder,
    scan_folder,
)
from tests.conftest import MakeImage, MakePdf, PageSizesOf


def _move(target: Path, dest: Path) -> Path:
    target.rename(dest)
    return dest


def test_scan_folder_alphabetical_case_insensitive(
    tmp_path: Path,
    make_pdf: MakePdf,
    make_image: MakeImage,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    a = make_image("png", name="a.png")
    b = make_pdf([(10, 10)], name="B.pdf")
    c = make_image("jpg", name="c.JPG")
    a = _move(a, folder / "a.png")
    b = _move(b, folder / "B.pdf")
    c = _move(c, folder / "c.JPG")

    result = scan_folder(folder)

    assert [p.name for p in result] == ["a.png", "B.pdf", "c.JPG"]


def test_scan_folder_excludes_merged_pdf(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    a = _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")
    _move(make_pdf([(20, 20)], name=MERGED_FILENAME), folder / MERGED_FILENAME)

    result = scan_folder(folder)

    assert [p.name for p in result] == [a.name]


def test_scan_folder_excludes_merged_pdf_case_insensitive(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")
    _move(make_pdf([(20, 20)], name="MERGED.PDF"), folder / "MERGED.PDF")

    result = scan_folder(folder)

    assert [p.name for p in result] == ["a.pdf"]


def test_scan_folder_ignores_unsupported(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="keep.pdf"), folder / "keep.pdf")
    (folder / "skip.txt").write_text("hi")
    (folder / "skip.gif").write_bytes(b"GIF89a")
    (folder / "skip.docx").write_bytes(b"PK")

    result = scan_folder(folder)

    assert [p.name for p in result] == ["keep.pdf"]


def test_scan_folder_no_recursion(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    sub = folder / "nested"
    sub.mkdir(parents=True)
    _move(make_pdf([(10, 10)], name="top.pdf"), folder / "top.pdf")
    _move(make_pdf([(20, 20)], name="deep.pdf"), sub / "deep.pdf")

    result = scan_folder(folder)

    assert [p.name for p in result] == ["top.pdf"]


def test_merge_folder_empty_raises_valueerror(tmp_path: Path) -> None:
    folder = tmp_path / "empty"
    folder.mkdir()

    with pytest.raises(ValueError, match="no supported files"):
        merge_folder(folder)


def test_merge_folder_missing_folder_raises_valueerror(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="folder not found"):
        merge_folder(tmp_path / "nope")


def test_merge_folder_combines_pdfs(
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(100, 200)], name="a.pdf"), folder / "a.pdf")
    _move(make_pdf([(300, 400), (500, 600)], name="b.pdf"), folder / "b.pdf")

    merge_folder(folder)

    merged = folder / MERGED_FILENAME
    assert merged.is_file()
    assert page_sizes_of(merged) == [(100, 200), (300, 400), (500, 600)]


def test_merge_folder_combines_pdf_and_image(
    tmp_path: Path,
    make_pdf: MakePdf,
    make_image: MakeImage,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(100, 200)], name="a.pdf"), folder / "a.pdf")
    _move(make_image("png", name="b.png"), folder / "b.png")

    merge_folder(folder)

    merged = folder / MERGED_FILENAME
    assert merged.is_file()
    reader = PdfReader(str(merged))
    assert len(reader.pages) == 2


def test_merge_folder_combines_jpg(
    tmp_path: Path,
    make_image: MakeImage,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_image("jpg", name="photo.jpg"), folder / "photo.jpg")

    merge_folder(folder)

    merged = folder / MERGED_FILENAME
    reader = PdfReader(str(merged))
    assert len(reader.pages) == 1


def test_merge_folder_handles_alpha_png(
    tmp_path: Path,
    make_image: MakeImage,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_image("rgba_png", name="screen.png"), folder / "screen.png")

    merge_folder(folder)

    merged = folder / MERGED_FILENAME
    reader = PdfReader(str(merged))
    assert len(reader.pages) == 1


def test_merge_folder_rejects_encrypted_pdf_member(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")

    encrypted = folder / "z_encrypted.pdf"
    base = make_pdf([(20, 20)], name="enc_src.pdf")
    from pypdf import PdfReader as R
    from pypdf import PdfWriter as W

    reader = R(str(base))
    writer = W()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password="pw")
    with encrypted.open("wb") as fh:
        writer.write(fh)

    with pytest.raises(ValueError, match="encrypted"):
        merge_folder(folder)


def test_merge_folder_atomic_no_tmp_left_on_success(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")

    merge_folder(folder)

    assert not (folder / (MERGED_FILENAME + TMP_SUFFIX)).exists()


def test_merge_folder_no_tmp_left_on_failure(
    tmp_path: Path,
    make_pdf: MakePdf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(10, 10)], name="a.pdf"), folder / "a.pdf")

    with (
        patch("app.pdf.merger._append_pdf", side_effect=ValueError("boom")),
        pytest.raises(ValueError, match="boom"),
    ):
        merge_folder(folder)

    assert not (folder / (MERGED_FILENAME + TMP_SUFFIX)).exists()
    assert not (folder / MERGED_FILENAME).exists()


def test_merge_folder_overwrites_existing_merged_pdf(
    tmp_path: Path,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    folder = tmp_path / "src"
    folder.mkdir()
    _move(make_pdf([(100, 200)], name="a.pdf"), folder / "a.pdf")
    stale = make_pdf([(999, 999)], name="stale_merged.pdf")
    shutil.move(str(stale), str(folder / MERGED_FILENAME))

    merge_folder(folder)

    merged = folder / MERGED_FILENAME
    assert page_sizes_of(merged) == [(100, 200)]
