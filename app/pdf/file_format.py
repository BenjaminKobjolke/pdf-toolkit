"""The document formats the viewer can open, and how to hand them to fitz.

One source of truth for "which file types are viewable" and the per-format quirk
that ``fitz`` needs: PDF and images open by extension, but text formats
(``.txt`` / ``.md``) are rendered by building a styled HTML document and opening
it via fitz's HTML engine (fitz has no Markdown reader). :func:`open_fitz`
centralizes that so no call site hardcodes it, and every consumer (render,
search, links, words) sees the same paginated result — important because the
font size affects pagination.

Adding a future format (e.g. docx) is one enum member here — plus a real render
path, since fitz cannot open docx.
"""

from __future__ import annotations

import io
from enum import StrEnum
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from app.config.text_view_settings import TextViewSettings
from app.pdf import text_html


class FileFormat(StrEnum):
    """A document format the viewer can open, keyed by its lowercase suffix."""

    PDF = ".pdf"
    TXT = ".txt"
    MD = ".md"
    PNG = ".png"
    JPG = ".jpg"
    JPEG = ".jpeg"
    GIF = ".gif"
    BMP = ".bmp"
    TIF = ".tif"
    TIFF = ".tiff"
    WEBP = ".webp"
    PSD = ".psd"

    @classmethod
    def of(cls, path: Path | None) -> FileFormat | None:
        """Return the format for ``path``'s suffix, or sniff unknown suffixes.

        A known suffix is trusted without looking at content. Unknown suffixes
        (``.ini``, ``.log``, …) fall back to a content sniff: plain UTF-8 text
        opens as :attr:`TXT`, anything else stays unsupported.
        """
        if path is None:
            return None
        try:
            return cls(path.suffix.lower())
        except ValueError:
            return cls.TXT if _looks_like_text(path) else None


TEXT_FORMATS = frozenset({FileFormat.TXT, FileFormat.MD})

# What renders as an image (fitz natively; PSD via the Pillow branch in
# open_fitz); deliberately wider than merge's img2pdf-convertible set
# (app/pdf/_inputs.py IMAGE_EXTENSIONS). Listed explicitly, not derived, so a
# future non-image member (e.g. DOCX) can't silently classify as an image.
IMAGE_FORMATS = frozenset(
    {
        FileFormat.PNG,
        FileFormat.JPG,
        FileFormat.JPEG,
        FileFormat.GIF,
        FileFormat.BMP,
        FileFormat.TIF,
        FileFormat.TIFF,
        FileFormat.WEBP,
        FileFormat.PSD,
    }
)

_SNIFF_BYTES = 8192


def _looks_like_text(path: Path) -> bool:
    """True if ``path``'s leading bytes are plain UTF-8 text (no null bytes).

    ``of`` is called speculatively (missing paths, directories), so I/O errors
    mean "not text" rather than raising. Non-UTF-8 text is rejected on purpose:
    :func:`open_fitz` reads text strictly as UTF-8 and would crash on it.
    """
    try:
        with path.open("rb") as fh:
            chunk = fh.read(_SNIFF_BYTES)
    except OSError:
        return False
    if not chunk or b"\x00" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError as exc:
        # A multibyte char cut off at the chunk boundary is still text.
        return exc.start >= len(chunk) - 3
    return True


# ponytail: single-window viewer, so one module-level setting is enough; make it
# per-window if the app ever opens multiple viewers. Defaults keep non-GUI
# callers (tests, CLI) on the plain light theme without any wiring.
_active_text_settings = TextViewSettings()


def set_text_view_settings(settings: TextViewSettings) -> None:
    """Set the text/markdown appearance applied by :func:`open_fitz`."""
    global _active_text_settings
    _active_text_settings = settings


def open_fitz(source: Path) -> fitz.Document:
    """Open ``source`` with fitz; render text formats as styled HTML.

    The single seam every fitz consumer routes through so ``.txt`` / ``.md`` open
    consistently (same layout everywhere) without per-site format logic.
    """
    fmt = FileFormat.of(source)
    if fmt in TEXT_FORMATS:
        html = text_html.render_html(
            source.read_text(encoding="utf-8"),
            is_markdown=fmt is FileFormat.MD,
            settings=_active_text_settings,
        )
        return fitz.open(stream=html.encode("utf-8"), filetype="html")
    if fmt is FileFormat.PSD:
        return fitz.open(stream=psd_to_png_bytes(source), filetype="png")
    return fitz.open(source, filetype=None)


def psd_to_png_bytes(source: Path) -> bytes:
    """Decode a PSD's merged composite with Pillow and re-encode as PNG bytes.

    fitz can't read PSD, so both render paths go through this: :func:`open_fitz`
    streams the bytes to fitz, and the viewer's working copy is written from them
    (making transforms/save-as operate on a plain PNG). PNG keeps alpha for the
    backdrop-compose path; CMYK/duotone must convert first (PNG can't encode
    them). PSDs saved without "Maximize Compatibility" have no composite — that
    and every other decode failure raises ``OSError`` so callers hit one
    corrupt-file surface.
    """
    try:
        with Image.open(source) as img:
            flat = img if img.mode in ("RGB", "RGBA") else img.convert("RGBA")
            buf = io.BytesIO()
            flat.save(buf, format="PNG")
        return buf.getvalue()
    except OSError:
        raise
    except Exception as exc:  # Pillow decode errors are not all OSError
        raise OSError(f"cannot read PSD {source.name}: {exc}") from exc
