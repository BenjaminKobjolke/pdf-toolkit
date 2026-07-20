"""Integration: rename / delete-saved-fields on the selected thumbnail.

Split from ``test_thumbnails_targeting`` (file-length cap); the grid helpers
and fixtures are shared from there.
"""

from __future__ import annotations

import pytest

from app.gui import commands
from app.gui.main_window import MainWindow
from app.pdf.image_spec import SidecarDocument
from app.pdf.sidecar import save_sidecar, sidecar_path
from tests.conftest import MakePdf, field_spec
from tests.integration.test_thumbnails_targeting import (  # noqa: F401 — fixture
    _enter_grid,
    _quiet_dialogs,
    _select,
)


def test_rename_selected_thumbnail_keeps_open_doc_and_grid(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import text_prompt_dialog

    other = make_pdf([(100, 100)], name="a.pdf")
    save_sidecar(other, SidecarDocument(fields=(field_spec(),)))
    doc = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    monkeypatch.setattr(text_prompt_dialog, "prompt_text", lambda *a, **k: "renamed.pdf")
    commands.find(window._registry, commands.RENAME_FILE).run()

    renamed = other.with_name("renamed.pdf")
    assert renamed.is_file()
    assert not other.exists()
    assert sidecar_path(renamed).is_file()
    assert window._source == doc
    assert window._thumbnails.is_active() is True
    assert window._thumbnails_view.currentItem().text() == "renamed.pdf"


def test_rename_selected_thumbnail_reports_error_when_target_exists(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import text_prompt_dialog

    other = make_pdf([(100, 100)], name="a.pdf")
    doc = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    monkeypatch.setattr(text_prompt_dialog, "prompt_text", lambda *a, **k: "b.pdf")
    commands.find(window._registry, commands.RENAME_FILE).run()

    assert other.is_file()
    assert window._thumbnails.is_active() is True


def test_rename_open_doc_selection_reopens_and_dismisses(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import text_prompt_dialog

    doc = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, doc)

    monkeypatch.setattr(text_prompt_dialog, "prompt_text", lambda *a, **k: "moved.pdf")
    commands.find(window._registry, commands.RENAME_FILE).run()

    assert window._source == doc.with_name("moved.pdf")
    assert window._thumbnails.is_active() is False


def test_delete_saved_fields_removes_selected_files_sidecar_only(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    other = make_pdf([(100, 100)], name="a.pdf")
    save_sidecar(other, SidecarDocument(fields=(field_spec(),)))
    doc = make_pdf([(100, 100)], name="b.pdf")
    save_sidecar(doc, SidecarDocument(fields=(field_spec(),)))
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    commands.find(window._registry, commands.DELETE_SAVED_FIELDS).run()

    assert not sidecar_path(other).is_file()
    assert sidecar_path(doc).is_file()  # the open doc's saved fields survive
    assert window.page_view.text_items()  # on-screen field untouched


def test_delete_saved_fields_on_open_doc_selection_clears_overlay(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    doc = make_pdf([(100, 100)], name="b.pdf")
    save_sidecar(doc, SidecarDocument(fields=(field_spec(),)))
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, doc)

    commands.find(window._registry, commands.DELETE_SAVED_FIELDS).run()

    assert window.page_view.text_items() == ()
