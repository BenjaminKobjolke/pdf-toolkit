"""Atomic in-place PDF writes shared across the core operations.

Several core ops (swap, delete, rotate, move, merge) finish the same way: write
the rebuilt document to a sibling ``.tmp`` file, then ``os.replace`` it so a
reader never sees a half-written PDF. This mirrors
:func:`app.io.json_store.write_json_atomic` for the JSON stores.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.io.fs import replace_atomic

_TMP_SUFFIX = ".tmp"


def write_pdf_atomic(source: Path, writer: PdfWriter) -> None:
    """Write ``writer`` to ``source`` atomically (``source.tmp`` then ``os.replace``)."""
    tmp = source.with_suffix(source.suffix + _TMP_SUFFIX)
    with tmp.open("wb") as fh:
        writer.write(fh)
    replace_atomic(tmp, source)


def write_text_atomic(source: Path, text: str) -> None:
    """Write ``text`` (UTF-8) to ``source`` atomically — the text-merge counterpart."""
    tmp = source.with_suffix(source.suffix + _TMP_SUFFIX)
    tmp.write_text(text, encoding="utf-8")
    replace_atomic(tmp, source)
