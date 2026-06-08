"""Unit tests for the GUI print action (offscreen Qt, PDF-output printer)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import fitz
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QWidget

from app.gui.print_actions import PrintActions
from tests.conftest import MakePdf


def test_print_document_no_source_does_nothing(qapp: object) -> None:
    """With no open document the dialog is never constructed."""
    parent = MagicMock(spec=QWidget)
    source = MagicMock(return_value=None)
    actions = PrintActions(parent, source)

    actions.print_document()  # must not raise / construct a printer

    source.assert_called_once()


def test_render_to_printer_emits_all_pages(qapp: object, make_pdf: MakePdf, tmp_path: Path) -> None:
    """The render loop paints every source page onto a PDF-output printer."""
    parent = MagicMock(spec=QWidget)
    actions = PrintActions(parent, MagicMock(return_value=None))
    source = make_pdf([(200, 300), (200, 300)])
    out = tmp_path / "out.pdf"

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(out))
    actions.render_to_printer(source, printer)

    assert out.is_file()
    doc = fitz.open(out)
    try:
        assert doc.page_count == 2
    finally:
        doc.close()
