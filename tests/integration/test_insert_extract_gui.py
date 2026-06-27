"""Integration tests for the GUI insert / extract page actions."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from app.config.settings import Settings
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, PageSizesOf, gui_settings, silence_dialogs


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return gui_settings(tmp_path)


@pytest.fixture
def window(qapp: object, settings: Settings, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    silence_dialogs(monkeypatch)
    return MainWindow(settings)


def _page_sizes(pdf: Path) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for page in PdfReader(str(pdf)).pages:
        box = page.mediabox
        out.append((float(box.width), float(box.height)))
    return out


def test_insert_is_deferred_and_follows_page(
    window: MainWindow,
    make_pdf: MakePdf,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.gui import file_dialogs

    pdf = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")
    original_bytes = pdf.read_bytes()
    window.open_pdf(pdf)
    window.page_view.go_to_page(1)  # current page = 2 (1-based)

    monkeypatch.setattr(file_dialogs, "prompt_open_file", lambda *a, **k: insert)
    window.page_actions.insert_pages()

    working = window._working_doc.working()
    assert working is not None
    assert _page_sizes(working) == [(10, 10), (20, 20), (99, 99), (30, 30)]
    # View follows the inserted page (now page 3).
    assert window.page_view.current_page_one_based() == 3
    # Deferred: original untouched until save.
    assert pdf.read_bytes() == original_bytes

    window.save_changes()
    assert _page_sizes(pdf) == [(10, 10), (20, 20), (99, 99), (30, 30)]


def test_extract_writes_new_file_and_leaves_original(
    window: MainWindow,
    make_pdf: MakePdf,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    page_sizes_of: PageSizesOf,
) -> None:
    from app.gui import file_dialogs

    pdf = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    original_bytes = pdf.read_bytes()
    out = tmp_path / "extracted.pdf"
    window.open_pdf(pdf)
    window.page_view.go_to_page(2)  # current page = 3

    monkeypatch.setattr(file_dialogs, "prompt_save_file", lambda *a, **k: out)
    window.page_actions.extract_current_page()

    assert page_sizes_of(out) == [(30, 30)]
    assert pdf.read_bytes() == original_bytes
    assert not window._working_doc.is_dirty()
