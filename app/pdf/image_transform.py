"""Rotate or flip an image file in place, preserving its format.

The image-document counterpart of :mod:`app.pdf.rotator` /
:mod:`app.pdf.flipper`: same atomic tmp-then-replace write, but the pixels
themselves are transformed (an image has no ``/Rotate`` flag to set).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from app.app_logger import log
from app.io.fs import replace_atomic

# ponytail: deliberate literal dup of _inputs.JPEG_FALLBACK_QUALITY — importing
# _inputs would drag img2pdf into every image transform for one int.
JPEG_SAVE_QUALITY = 95

_TMP_SUFFIX = ".tmp"

# Pillow's Transpose.ROTATE_* constants are counterclockwise; ours are clockwise
# to match app.pdf.rotator's vocabulary (ROTATE_RIGHT=90 etc.).
_CLOCKWISE_TO_TRANSPOSE = {
    90: Image.Transpose.ROTATE_270,
    180: Image.Transpose.ROTATE_180,
    270: Image.Transpose.ROTATE_90,
}


def rotate_image(source: Path, degrees: int) -> None:
    """Rotate the image at ``source`` by ``degrees`` clockwise, overwriting atomically.

    Raises ``ValueError`` if ``degrees`` is not 90, 180, or 270.
    """
    method = _CLOCKWISE_TO_TRANSPOSE.get(degrees % 360)
    if method is None:
        raise ValueError(f"rotation must be a multiple of 90, got {degrees}")
    log.info("rotating image %s clockwise: %s", degrees, source)
    _transpose(source, method)


def flip_image(source: Path, *, horizontal: bool) -> None:
    """Mirror the image at ``source`` (left-right or top-bottom), overwriting atomically."""
    method = Image.Transpose.FLIP_LEFT_RIGHT if horizontal else Image.Transpose.FLIP_TOP_BOTTOM
    log.info("flipping image %s: %s", "horizontally" if horizontal else "vertically", source)
    _transpose(source, method)


def _transpose(source: Path, method: Image.Transpose) -> None:
    with Image.open(source) as img:
        fmt = img.format
        # Bake any EXIF orientation into the pixels first so the transform
        # applies to what viewers display, not the raw sensor orientation.
        upright = ImageOps.exif_transpose(img)
        result = upright.transpose(method)
    tmp = source.with_suffix(source.suffix + _TMP_SUFFIX)
    save_args = {"quality": JPEG_SAVE_QUALITY} if fmt == "JPEG" else {}
    result.save(tmp, format=fmt, **save_args)
    replace_atomic(tmp, source)
