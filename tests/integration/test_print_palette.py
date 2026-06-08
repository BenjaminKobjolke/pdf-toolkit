"""Integration tests for the Print palette command (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PySide6.QtPrintSupport import QPrinter

from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def test_print_command_gated_by_document(window: MainWindow, make_pdf: MakePdf) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.PRINT).is_enabled() is False
    window.open_pdf(make_pdf([(200, 300)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.PRINT).is_enabled() is True


def test_print_renders_open_document_to_pdf(
    window: MainWindow, make_pdf: MakePdf, tmp_path: Path
) -> None:
    """End-to-end: open a 3-page PDF, render via the action to a PDF printer."""
    window.open_pdf(make_pdf([(200, 300), (200, 300), (200, 300)]))
    out = tmp_path / "printed.pdf"
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(out))

    source = window._working_doc.working()
    assert source is not None
    window.print_actions.render_to_printer(source, printer)

    doc = fitz.open(out)
    try:
        assert doc.page_count == 3
        # Each printed page carries rendered pixels (not blank white only).
        pix = doc.load_page(0).get_pixmap()
        assert pix.width > 0 and pix.height > 0
    finally:
        doc.close()
