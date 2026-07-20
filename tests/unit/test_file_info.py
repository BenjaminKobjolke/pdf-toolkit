"""Unit tests for app.gui.file_info (metadata row collection)."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.gui import file_info
from app.gui.file_info import FileInfoDialog, _human_size, collect_file_info
from app.gui.filter_list_dialog import FilterListOptions, ListEntry
from tests.conftest import MakeImage, MakePdf


def _labels(fields: list[file_info.FileInfoField]) -> dict[str, str]:
    return {f.label: f.value for f in fields}


def test_human_size_boundaries() -> None:
    assert _human_size(500) == "500 B"
    assert _human_size(1536) == "1.5 KB"
    assert _human_size(1048576) == "1.0 MB"


def test_collect_pdf_core_and_dimensions(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])

    fields = collect_file_info(pdf, page_index=0)
    values = _labels(fields)

    assert values["Name"] == pdf.name
    assert values["Path"] == str(pdf)
    assert values["Format"] == "PDF"
    assert values["Pages"] == "2"
    assert values["Current page"] == "1"
    assert values["Width"] == "100 pt"
    assert values["Height"] == "200 pt"


def test_collect_pdf_metadata_only_when_present(tmp_path: Path) -> None:
    target = tmp_path / "meta.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_metadata({"/Title": "My Title", "/Author": "Jane Doe"})
    with target.open("wb") as fh:
        writer.write(fh)

    values = _labels(collect_file_info(target, page_index=0))

    assert values["Title"] == "My Title"
    assert values["Author"] == "Jane Doe"
    assert "Subject" not in values  # empty metadata fields are omitted


def test_collect_image_uses_pixels_and_no_pdf_metadata(make_image: MakeImage) -> None:
    img = make_image("png", size=(16, 24))

    values = _labels(collect_file_info(img, page_index=0))

    assert values["Format"] == "PNG"
    assert values["Width"] == "16 px"
    assert values["Height"] == "24 px"
    assert "Pages" not in values  # page counts only make sense for PDFs
    assert "Current page" not in values
    assert "Title" not in values
    assert "Author" not in values


def test_dialog_enter_copies_value_and_stays_open(qapp: object) -> None:
    copied: list[str] = []
    entries = [
        ListEntry(title="Width: 100 pt", payload="100 pt"),
        ListEntry(title="Height: 200 pt", payload="200 pt"),
    ]
    dialog = FileInfoDialog(entries, FilterListOptions(), copied.append)

    dialog.accept_current()  # Enter on the first row

    assert copied == ["100 pt"]
    assert dialog.isVisible() is False  # never shown, but must not have accepted/closed
    assert dialog.result() == 0  # QDialog.Rejected default — Enter did not accept
    assert dialog._list.item(0).text() == "Width: 100 pt   ✓ copied"


def test_dialog_marker_clears_when_selection_moves(qapp: object) -> None:
    entries = [ListEntry(title="A: 1", payload="1"), ListEntry(title="B: 2", payload="2")]
    dialog = FileInfoDialog(entries, FilterListOptions(), lambda _v: None)

    dialog.accept_current()  # marks row 0
    dialog.move_selection(1)  # move to row 1 → row 0 marker cleared

    assert dialog._list.item(0).text() == "A: 1"


def test_reader_still_reads_metadata_pdf(tmp_path: Path) -> None:
    """Guard the fixture: the metadata PDF is a valid, readable PDF."""
    target = tmp_path / "ok.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with target.open("wb") as fh:
        writer.write(fh)

    assert len(PdfReader(str(target)).pages) == 1
