"""UI strings for the OCR-image command.

Kept out of ``strings.py``, which is already at the file-length cap, matching
the existing domain string modules (``file_strings``, ``overlay_strings``).
"""

from __future__ import annotations

CMD_OCR_IMAGE = "OCR image (extract text)…"
CMD_OCR_LANGUAGE = "OCR: language…"

DIALOG_OCR_LANGUAGE_TITLE = "OCR language"
OCR_LANGUAGE_PLACEHOLDER = "Type to filter languages…"
LABEL_OCR_LANG_AUTO = "Automatic (Windows profile languages)"

PICK_TITLE = "OCR result — Enter chooses, Esc closes"
PICK_PLACEHOLDER = "Copy or save…"
OPT_COPY = "Copy text to clipboard"
OPT_SAVE_FMT = "Save as {name}"

CONFIRM_OVERWRITE_TITLE = "Overwrite file"
CONFIRM_OVERWRITE_FMT = "{name} already exists. Overwrite it?"

MSG_OCR_COPIED = "copied OCR text to clipboard"
MSG_OCR_SAVED_FMT = "saved OCR text to: {name}"
MSG_OCR_NO_TEXT = "no text recognized in this image"
MSG_OCR_UNAVAILABLE = "OCR is not available (requires Windows built-in OCR)"
MSG_OCR_FAILED_FMT = "OCR failed: {error}"
