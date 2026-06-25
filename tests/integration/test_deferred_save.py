"""Integration tests for the deferred (temp working copy) save workflow."""

from __future__ import annotations

import os
import stat
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
    # The viewer surfaces results/confirmations through modal dialogs, which would
    # block headless tests. Auto-dismiss them (confirm -> Save/primary).
    silence_dialogs(monkeypatch)
    return MainWindow(settings)


def _rotations(pdf: Path) -> list[int]:
    return [page.rotation for page in PdfReader(str(pdf)).pages]


def test_rotate_is_deferred_until_save(
    window: MainWindow, settings: Settings, make_pdf: MakePdf
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])
    original_bytes = pdf.read_bytes()
    window.open_pdf(pdf)

    window.rotate_actions.rotate_right()

    # The working copy is rotated, but the original on disk is untouched.
    assert window._working_doc.is_dirty()
    assert pdf.read_bytes() == original_bytes
    working = window._working_doc.working()
    assert working is not None
    assert _rotations(working) == [90, 0]

    window.save_changes()

    assert not window._working_doc.is_dirty()
    assert _rotations(pdf) == [90, 0]
    assert len(list(settings.backup_dir.glob("*.pdf"))) == 1


def test_move_to_last_follows_page_and_defers(
    window: MainWindow, make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    pdf = make_pdf([(10, 10), (20, 20), (30, 30)])
    original_bytes = pdf.read_bytes()
    window.open_pdf(pdf)

    window.move_actions.move_to_last()  # page 1 -> last

    working = window._working_doc.working()
    assert working is not None
    assert page_sizes_of(working) == [(20, 20), (30, 30), (10, 10)]
    # View follows the moved page (now last, 1-based index 3).
    assert window._page_view.current_page_one_based() == 3
    assert pdf.read_bytes() == original_bytes  # original deferred

    window.save_changes()
    assert page_sizes_of(pdf) == [(20, 20), (30, 30), (10, 10)]


def test_rotate_and_save_readonly_pdf(
    window: MainWindow, settings: Settings, make_pdf: MakePdf
) -> None:
    # PDFs from email attachments / downloads commonly carry the read-only
    # attribute. The working copy inherits it; without clearing it, the atomic
    # os.replace fails with WinError 5 on Windows.
    pdf = make_pdf([(100, 200), (300, 400)])
    os.chmod(pdf, stat.S_IREAD)
    window.open_pdf(pdf)

    window.rotate_actions.rotate_right()
    window.save_changes()

    assert not window._working_doc.is_dirty()
    assert _rotations(pdf) == [90, 0]
    working = window._working_doc.working()
    assert working is not None
    assert list(working.parent.glob("*.tmp")) == []


def test_discard_path_leaves_original_unchanged(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])
    original_bytes = pdf.read_bytes()
    window.open_pdf(pdf)
    window.rotate_actions.rotate_right()

    # Simulate "Discard": drop the dirty flag without saving, then close.
    window._working_doc.discard()
    window._working_doc.close()

    assert pdf.read_bytes() == original_bytes
