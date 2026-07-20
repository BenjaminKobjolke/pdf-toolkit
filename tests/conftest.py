"""Shared pytest fixtures for unit and integration tests."""

from __future__ import annotations

import os
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.pdf.text_spec import TextFieldSpec
    from app.storage.backend import StorageBackend

# Qt must run headless in tests; set before any QApplication is constructed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp() -> Iterator[object]:
    """Provide a single offscreen QApplication for the whole test session."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def silence_dialogs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-dismiss the custom confirm/alert dialogs so headless tests don't block.

    Confirmations resolve to the primary button (Yes/Save) and alerts become no-ops.
    Tests that need a specific confirm result (e.g. Yes/No/Cancel) or that inspect an
    alert's text should patch ``app.gui.confirm_dialog`` themselves instead.
    """
    from app.gui import confirm_dialog

    monkeypatch.setattr(confirm_dialog, "show_message", lambda *a, **k: None)
    monkeypatch.setattr(
        confirm_dialog, "confirm", lambda *a, **k: confirm_dialog.DialogResult.PRIMARY
    )


def gui_settings(tmp_path: Path) -> Settings:
    """Settings pointing at a per-test SQLite DB so GUI tests stay hermetic."""
    from app.config.settings import Settings

    return Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        database_url=f"sqlite:///{tmp_path / 'pdf-toolkit.db'}",
    )


def gui_backend(tmp_path: Path) -> StorageBackend:
    """A storage backend on the same per-test DB the window uses.

    Tests that assert what a controller persisted open this to read the DB the
    window wrote to (deterministic from ``tmp_path``).
    """
    from app.storage.factory import make_backend

    return make_backend(gui_settings(tmp_path).database_url)


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> object:
    """A fresh viewer window backed by per-test temp settings (all stores)."""
    from app.gui.main_window import MainWindow

    return MainWindow(gui_settings(tmp_path))


def field_spec() -> TextFieldSpec:
    """A minimal saved text-field spec for sidecar-writing tests."""
    from app.pdf.text_spec import TextFieldSpec

    return TextFieldSpec(
        page_index=0,
        x=20.0,
        y=30.0,
        width=0.0,
        height=0.0,
        text="Saved",
        font_family="Helvetica",
        font_size=18.0,
        color="#000000",
        bg_color=None,
        bold=False,
        italic=False,
    )


PageSize = tuple[float, float]
ImageKind = Literal["png", "jpg", "rgba_png"]


class MakePdf(Protocol):
    def __call__(self, page_sizes: Sequence[PageSize], name: str | None = ...) -> Path: ...


class PageSizesOf(Protocol):
    def __call__(self, pdf: Path) -> list[PageSize]: ...


class MakeImage(Protocol):
    def __call__(
        self,
        kind: ImageKind = ...,
        name: str | None = ...,
        size: tuple[int, int] = ...,
    ) -> Path: ...


class MakeSearchablePdf(Protocol):
    def __call__(self, page_texts: Sequence[str], name: str | None = ...) -> Path: ...


def _build_pdf(target: Path, page_sizes: Sequence[PageSize]) -> Path:
    writer = PdfWriter()
    for width, height in page_sizes:
        writer.add_blank_page(width=width, height=height)
    with target.open("wb") as fh:
        writer.write(fh)
    return target


@pytest.fixture
def make_pdf(tmp_path: Path) -> MakePdf:
    """Factory: produce a PDF in tmp with the given per-page (width, height) sizes.

    Distinct sizes per page let tests verify page identity after swap/delete without OCR.
    """
    counter = {"n": 0}

    def _factory(page_sizes: Sequence[PageSize], name: str | None = None) -> Path:
        counter["n"] += 1
        filename = name or f"sample_{counter['n']}.pdf"
        return _build_pdf(tmp_path / filename, page_sizes)

    return _factory


@pytest.fixture
def make_image(tmp_path: Path) -> MakeImage:
    """Factory: produce a tiny image file (PNG, JPG, or RGBA PNG) in tmp_path."""
    counter = {"n": 0}

    def _factory(
        kind: ImageKind = "png",
        name: str | None = None,
        size: tuple[int, int] = (16, 16),
    ) -> Path:
        counter["n"] += 1
        if kind == "jpg":
            ext = ".jpg"
            mode = "RGB"
            color: tuple[int, ...] = (200, 100, 50)
        elif kind == "rgba_png":
            ext = ".png"
            mode = "RGBA"
            color = (10, 200, 50, 128)
        else:
            ext = ".png"
            mode = "RGB"
            color = (50, 100, 200)
        filename = name or f"image_{counter['n']}{ext}"
        target = tmp_path / filename
        Image.new(mode, size, color).save(target)
        return target

    return _factory


@pytest.fixture
def make_searchable_pdf(tmp_path: Path) -> MakeSearchablePdf:
    """Factory: produce a PDF whose pages contain real, searchable text.

    ``make_pdf`` writes blank pages (pypdf); full-text search tests need actual
    glyphs, so this writes one text string per page via fitz ``insert_text``.
    """
    import fitz

    counter = {"n": 0}

    def _factory(page_texts: Sequence[str], name: str | None = None) -> Path:
        counter["n"] += 1
        filename = name or f"searchable_{counter['n']}.pdf"
        target = tmp_path / filename
        doc = fitz.open()
        try:
            for text in page_texts:
                page = doc.new_page()
                page.insert_text((50, 80), text, fontsize=14)
            doc.save(str(target))
        finally:
            doc.close()
        return target

    return _factory


@pytest.fixture
def page_sizes_of() -> PageSizesOf:
    """Read a PDF and return its page sizes as (width, height) floats."""

    def _read(pdf: Path) -> list[PageSize]:
        reader = PdfReader(str(pdf))
        out: list[PageSize] = []
        for page in reader.pages:
            box = page.mediabox
            out.append((float(box.width), float(box.height)))
        return out

    return _read
