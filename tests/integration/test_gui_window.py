"""Integration tests for the GUI window wiring (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from app.config.settings import Settings
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, PageSizesOf


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    settings = Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
    )
    return MainWindow(settings)


def test_delete_current_page_shrinks_document(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    window.open_pdf(pdf)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)

    window.page_actions.delete_current_page()

    assert page_sizes_of(pdf) == [(300, 400), (120, 120)]
    assert window._page_view.total_pages() == 2


def test_swap_pages_through_window(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])
    window.open_pdf(pdf)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)

    window.page_actions.swap()

    assert page_sizes_of(pdf) == [(300, 400), (100, 200)]


def test_invalid_swap_reports_error_and_keeps_file(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    window.open_pdf(pdf)
    captured: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, msg, *a, **k: captured.append(msg)
    )

    window.page_actions.swap()

    assert captured  # an error dialog was shown
    assert page_sizes_of(pdf) == [(100, 200), (300, 400), (120, 120)]
