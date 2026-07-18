"""Mirror a single page of a PDF in place."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter, Transformation

from app.pdf._atomic import write_pdf_atomic
from app.pdf._inputs import check_first_page, check_page_in_range, open_reader


def flip_page(source: Path, page_number: int, *, horizontal: bool) -> None:
    """Mirror ``page_number`` (1-based) left-right or top-bottom, overwriting atomically.

    Raises ``ValueError`` if the page number is < 1 or exceeds the page count,
    or the PDF is encrypted.
    """
    check_first_page(page_number)

    reader = open_reader(source)
    check_page_in_range(page_number, len(reader.pages), source)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    target = writer.pages[page_number - 1]
    # Bake any /Rotate flag into the content first so "horizontal" mirrors the
    # page as displayed, not the pre-rotation coordinate system.
    target.transfer_rotation_to_content()
    box = target.mediabox
    if horizontal:
        mirror = Transformation().scale(-1, 1).translate(float(box.left) + float(box.right), 0)
    else:
        mirror = Transformation().scale(1, -1).translate(0, float(box.bottom) + float(box.top))
    target.add_transformation(mirror)

    write_pdf_atomic(source, writer)
