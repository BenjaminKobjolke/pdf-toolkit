"""Shared pytest fixtures for unit and integration tests."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

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
