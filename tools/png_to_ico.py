"""Convert a source PNG into a multi-resolution Windows ``.ico``.

Used to produce ``assets/icon.ico`` from a user-supplied ``assets/icon.png``.
The same ``.ico`` drives both the runtime Qt window icon and the embedded
PyInstaller exe icon (see ``FastFileViewer.spec``).

Run via ``tools/png_to_ico.bat``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image

from app.app_logger import configure_logging

logger = logging.getLogger("png_to_ico")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PNG = PROJECT_ROOT / "assets" / "icon.png"
DEFAULT_ICO = PROJECT_ROOT / "assets" / "icon.ico"
ICON_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def convert(src: Path, dst: Path) -> None:
    """Write a multi-size ``.ico`` at ``dst`` from the PNG at ``src``."""
    if not src.is_file():
        raise FileNotFoundError(f"Source PNG not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as opened:
        image = opened.convert("RGBA")
        side = max(image.size)
        if image.size != (side, side):
            canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
            image = canvas
        image.save(dst, format="ICO", sizes=ICON_SIZES)
    logger.info("Wrote %s (sizes: %s)", dst, ", ".join(f"{w}x{h}" for w, h in ICON_SIZES))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a PNG to a multi-size .ico.")
    parser.add_argument("png", nargs="?", type=Path, default=DEFAULT_PNG, help="source PNG")
    parser.add_argument("ico", nargs="?", type=Path, default=DEFAULT_ICO, help="output ICO")
    args = parser.parse_args(argv)

    configure_logging("INFO")
    try:
        convert(args.png, args.ico)
    except (FileNotFoundError, OSError) as exc:
        logger.error("Conversion failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
