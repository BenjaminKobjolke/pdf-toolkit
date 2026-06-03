"""Centralized UI string constants for the GUI viewer."""

from __future__ import annotations

WINDOW_TITLE = "pdf-toolkit viewer"

MENU_FILE = "&File"
ACTION_OPEN = "Open PDF…"
ACTION_QUIT = "Quit"

BTN_PREV = "◀ Prev"
BTN_NEXT = "Next ▶"
BTN_SWAP = "Swap 2 pages"
BTN_DELETE_PAGE = "Delete current page"
BTN_DELETE_RANGE = "Delete range…"
BTN_MERGE_FOLDER = "Merge folder…"

FILE_FILTER_PDF = "PDF files (*.pdf)"
DIALOG_OPEN_TITLE = "Open PDF"
DIALOG_MERGE_TITLE = "Choose folder to merge"
DIALOG_RANGE_TITLE = "Delete page range"
PROMPT_RANGE_START = "Start page (1-based, inclusive):"
PROMPT_RANGE_END = "End page (1-based, inclusive):"
CONFIRM_TITLE = "Confirm"
CONFIRM_DELETE_PAGE_FMT = "Delete page {page} of {total}?"

DIALOG_ERROR_TITLE = "Operation failed"
DIALOG_SUCCESS_TITLE = "Done"

LABEL_NO_DOC = "No PDF open"
LABEL_PAGE_FMT = "Page {current} / {total}"

MSG_NOT_FOUND_FMT = "input file not found: {path}"
MSG_BACKUP_FAILED_FMT = "failed to create backup: {error}"
MSG_DONE_FMT = "done: {name}"
MSG_MERGED_FMT = "merged: {path}"
