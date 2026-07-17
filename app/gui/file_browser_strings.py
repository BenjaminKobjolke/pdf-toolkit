"""UI strings and filter presets for the custom file browser dialog.

Mirrors ``file_strings.py``: keeps these out of ``strings.py`` (at the length
cap). The :class:`FileFilter` presets replace the old Qt-style filter strings,
so callers pass a typed value, not a raw ``"PDF files (*.pdf)"`` string.
"""

from __future__ import annotations

from app.gui.file_browser_model import FileFilter
from app.pdf.file_format import IMAGE_FORMATS

FILTER_PDF = FileFilter("PDF files", (".pdf",))
# Every image format the viewer renders — derived so the two can't drift apart.
FILTER_VIEWER_IMAGES = FileFilter("Images", tuple(sorted(fmt.value for fmt in IMAGE_FORMATS)))
# Label for the user-configurable open-dialog filter (see OpenFilterController).
OPEN_FILTER_LABEL = "Documents"
FILTER_INSERT = FileFilter("PDF or image", (".pdf", ".jpg", ".jpeg", ".png"))
FILTER_IMAGE = FileFilter("Images", (".png", ".jpg", ".jpeg"))
FILTER_ALL = FileFilter("All files", ())

FILTER_PLACEHOLDER = "type to filter…"
UP_NAME = ".."
# Top row in directory mode; brackets keep it from colliding with a real name.
CHOOSE_DIR_LABEL = "[ use this folder ]"
DRIVES_LABEL = "Drives"

KEY_HINT = (
    "j/k or ↑/↓ move   l/→/⏎ open   h/←/Alt+↑ or .. up a level\n"
    "/ filter   gg first   G last   Esc/q cancel"
)
SAVE_KEY_HINT = (
    "j/k or ↑/↓ move   l/→ open dir   ⏎ choose   h/←/Alt+↑ or .. up\n"
    "Tab edit name   / filter   gg/G first/last   Esc cancel"
)
