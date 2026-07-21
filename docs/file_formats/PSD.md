# Photoshop (`.psd`)

fitz can't read PSD, so the viewer renders the file's **merged composite**
(the stored full-resolution preview — what IrfanView shows) via Pillow:
`psd_to_png_bytes` in `app/pdf/file_format.py` decodes it and re-encodes as
PNG.

- **Thumbnails grid**: the PNG bytes are streamed to fitz in memory — no file
  is created.
- **Open document**: the working copy is written as a **PNG conversion**
  (`app/gui/working_document.py`) into the session temp dir — same lifecycle
  as every other format's working copy (auto-deleted on switch/close), and the
  reason all image machinery below just works.

## Preview-only editing

**Rotate / flip work**, operating on the PNG working copy — but Pillow cannot
*write* PSD, so they are **preview-only**:

- No **Save** command; the original `.psd` is never modified.
- The footer never shows **● Modified** and switching/closing never prompts —
  transforms are silently discarded (`WorkingDocument.mark_dirty` is a no-op
  for PSD).
- **Save As** is the escape hatch: it exports the current preview —
  including applied rotate/flip — as a `.png` (the suggested filename is
  `<name>.png` so the bytes match the extension).

## Failure modes

PSDs saved without **"Maximize Compatibility"** have no composite — the open
fails with a warning dialog (`could not open <name>: …`), leaving the
previously open document intact. CMYK/duotone PSDs are converted to RGBA
before PNG encoding.

## Gating

`SAVEABLE` (= `TRANSFORMABLE` minus PSD) gates **Save** in
`app/gui/commands.py`; rotate/flip/Save As stay `TRANSFORMABLE`. Tests:
`tests/unit/test_working_document.py`, `tests/unit/test_command_formats.py`,
PSD cases in `tests/integration/test_gui_window.py`.
