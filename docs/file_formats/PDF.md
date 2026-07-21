# PDF (`.pdf`)

The viewer's native format — every feature works here. Rendered directly by
fitz (PyMuPDF); all edits are deferred to a temp working copy until **Save
changes to original file** (`Ctrl+S`), which backs the original up first
(`backup/YYYYMMDD-HHMM-<name>.pdf`).

## PDF-only features

- **Page operations** — delete (single / range), insert, extract, swap, move,
  reorder. See `../COMMAND_PALETTE.md`.
- **Rotate / flip** — sets/bakes the page's `/Rotate` flag rather than touching
  pixels (`app/pdf/rotator.py`, `app/pdf/flipper.py`).
- **Edit mode** — text fields, placed images, rectangles, export-to-PDF; layout
  persists in a JSON sidecar next to the PDF. See `../edit_mode/EDIT_MODE.md`.
- **PDF metadata** — title/author/subject/… shown in **File information**.

## Shared with text formats (`HAS_TEXT`)

Full-text search (`Ctrl+F`), open/copy link (vim-style hints, both annotation
links and bare URLs in the text), select mode, copy page text.

## Everything else

Navigation, zoom, print, copy page/view as image, rename/delete, thumbnails,
Save / Save As — see the capability table in `../FILE_FORMATS.md`.
