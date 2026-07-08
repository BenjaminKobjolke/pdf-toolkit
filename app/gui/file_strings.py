"""UI strings for the file-utility commands (save-as, clipboard, open folder).

Kept out of ``strings.py``, which is already at the file-length cap, matching the
existing domain string modules (``overlay_strings``, ``default_app_strings``).
"""

from __future__ import annotations

CMD_SAVE_AS = "Save file as…"
CMD_COPY_FILE_PATH = "Copy file path to clipboard"
CMD_COPY_FILE_NAME = "Copy file name to clipboard"
CMD_COPY_FILE_NAME_NO_EXT = "Copy file name without extension to clipboard"
CMD_COPY_PAGE_TEXT = "Copy all text from current page"
CMD_OPEN_FOLDER = "Open containing folder"

DIALOG_SAVE_AS_TITLE = "Save file as"

MSG_SAVED_AS_FMT = "saved a copy to: {name}"
MSG_COPIED_PATH = "copied file path to clipboard"
MSG_COPIED_NAME = "copied file name to clipboard"
MSG_COPIED_NAME_NO_EXT = "copied file name (no extension) to clipboard"
MSG_COPIED_PAGE_TEXT = "copied page text to clipboard"
MSG_NO_PAGE_TEXT = "this page has no selectable text"
MSG_OPEN_FOLDER_FAILED_FMT = "could not open folder: {error}"
