# File Formats (multi-format viewer)

The GUI viewer opens **PDF, plain-text (`.txt`), Markdown (`.md`), and image
(`.png` `.jpg` `.jpeg` `.gif` `.bmp` `.tif` `.tiff` `.webp` `.psd`)** documents — plus
**any other plain-text file** (`.ini`, `.log`, `.json`, …) via a content sniff
(see *Opening a file*). Each command declares which formats it supports, so a
feature is reachable only for the formats it actually works on.

Per-format details live in `file_formats/`:

| Format | Doc |
|--------|-----|
| PDF (`.pdf`) | [file_formats/PDF.md](file_formats/PDF.md) |
| Text / Markdown (`.txt`, `.md`, sniffed plain-text) | [file_formats/TEXT.md](file_formats/TEXT.md) |
| Images (`.png` `.jpg` `.jpeg` `.gif` `.bmp` `.tif` `.tiff` `.webp`) | [file_formats/IMAGES.md](file_formats/IMAGES.md) |
| Photoshop (`.psd`) | [file_formats/PSD.md](file_formats/PSD.md) |

## What works per format

| Feature | PDF | txt | md | img |
|---------|:---:|:---:|:--:|:---:|
| View / navigate / zoom | ✅ | ✅ | ✅ | ✅ |
| Dark mode + font size (palette) | — | ✅ | ✅ | — |
| Formatted rendering (`##`→heading) | — | — | ✅ | — |
| Search text (`Ctrl+F`) | ✅ | ✅ | ✅ | — |
| Open / copy link (vim hints) | ✅ | ✅ | ✅ | — |
| Select mode (vim-style copy) | ✅ | ✅ | ✅ | — |
| Copy page text | ✅ | ✅ | ✅ | — |
| Copy file path / name | ✅ | ✅ | ✅ | ✅ |
| Copy page / current view as image | ✅ | ✅ | ✅ | ✅ |
| Print, rename, open folder | ✅ | ✅ | ✅ | ✅ |
| Delete / insert / extract / swap / move page | ✅ | — | — | — |
| Rotate / flip (page for PDFs, whole image for img) | ✅ | — | — | ✅ (PSD: preview-only) |
| Edit mode (text fields, images, rectangles), export | ✅ | — | — | — |
| Save / Save As | ✅ | — | — | ✅ (PSD: no Save; Save As exports `.png`) |
| Merge folder | ✅ (→ `merged.pdf`) | ✅ (→ `merged.txt`) | ✅ (→ `merged.md`) | ✅ (→ `merged.pdf`, png/jpg/jpeg only) |

Commands that don't apply to the open document's format are greyed out in the
command palette and their keyboard shortcuts are no-ops. Format-agnostic commands
(Open, Exit, settings, toggles) are always available.

## Opening a file

- The **Open** dialog's filter is **user-configurable**: by default it lists
  `.pdf`, `.txt`, `.md`, and the image extensions; **Open dialog: toggle all files** switches to
  listing everything, and **Open dialog: file extensions…** edits the extension
  list (e.g. `pdf, txt, md, ini`). Both persist across sessions and reset from
  **Remembered settings…** ("Open dialog filter").
- Passing a path on the command line — `FastFileViewer.bat notes.md` — opens it directly.
- **Next / previous file in directory** (Alt+Right / Alt+Left) steps through the
  same filter's matches in the current document's folder, skipping files that
  fail the content sniff.
- **Unknown extensions are content-sniffed**: if the file's leading bytes are plain
  UTF-8 text (no null bytes), it opens as a `.txt`-style document — so `.ini`,
  `.log`, `.cfg`, `.json`, … just work. Binary or non-UTF-8 files are rejected
  with a warning rather than handed to the renderer to fail obscurely. A known
  suffix always wins — a `.pdf` or `.png` is never sniffed.
- To open files by **double-click from Explorer**, associate their types with the
  viewer via **File type associations…** (Windows only; see `FILE_ASSOCIATIONS.md`).

## Merging text folders

*Merge folder…* dispatches on the folder's contents:

- A folder of **PDFs / images** → `merged.pdf` (pages concatenated).
  Merge accepts only `.png`/`.jpg`/`.jpeg` images (the `img2pdf` conversion set) —
  deliberately narrower than what the viewer can *display* (`IMAGE_FORMATS`).
- A folder of **text files** (`.txt` / `.md`) → `merged.<ext>`: the files are read
  as UTF-8 and concatenated (blank line between files). The output extension is the
  shared one when uniform (all `.md` → `merged.md`), otherwise `.txt`.
- A folder **mixing** text with PDF/image files is refused.

This applies to the CLI `pdf-merge-folder.bat` too — it shares the same backend.

## How it fits together

- `app/pdf/file_format.py` — the `FileFormat` enum (`.pdf` / `.txt` / `.md` / the
  image suffixes), the `TEXT_FORMATS` / `IMAGE_FORMATS` capability sets,
  `FileFormat.of(path)` (suffix → format; an unknown suffix falls back to a content
  sniff — first 8KB, no null bytes, valid UTF-8 → `TXT` — else `None`), and
  `open_fitz(source)`. `open_fitz` is the single seam every fitz consumer uses; for
  text formats it builds a styled HTML document (via `app/pdf/text_html.py`) and opens
  it with `filetype="html"`. Images take the plain `fitz.open` path (fitz renders
  them natively as one page); PSD and WebP go through `to_png_bytes` — fitz's
  bundled MuPDF cannot decode either (see
  [file_formats/PSD.md](file_formats/PSD.md)). Unit-tested in
  `tests/unit/test_file_format.py`.
- `app/pdf/text_html.py` — `render_html(text, is_markdown, settings)`: markdown → HTML
  (the `markdown` package) or plain text → `<pre>`, wrapped in one CSS `<style>` that
  owns font size, the light/dark theme, and heading/code styling. Pure; unit-tested in
  `tests/unit/test_text_html.py`.
- `app/config/text_view_settings.py` — `TextViewSettings` (`font_pt`, `dark_mode`) +
  its store, persisted like the other appearance settings; edited via
  `app/gui/text_view_controller.py` and the two palette commands
  (**Text/Markdown: toggle dark mode** / **font size…**, gated to `.txt`/`.md`).
- `app/config/open_filter_settings.py` — `OpenFilterSettings` (`all_files`,
  `extensions`; defaults derived from the `FileFormat` enum) + its store, and
  `parse_extensions("pdf, ini")` → `(".pdf", ".ini")`. Edited via
  `app/gui/open_filter_controller.py` and the two **Open dialog:** palette
  commands; `MainWindow.open_pdf` asks the controller for the current
  `FileFilter`. Unit-tested in `tests/unit/test_open_filter_settings.py`.
- `app/gui/commands.py` — each `Command` carries a `formats` field (`None` =
  agnostic, `PDF_ONLY`, `HAS_TEXT` = pdf/txt/md, `VIEWABLE` = everything
  renderable including images, `TRANSFORMABLE` = pdf + images for rotate/flip,
  or `SAVEABLE` = `TRANSFORMABLE` minus PSD for Save) and a `available(fmt)` gate.
  The command palette (`palette_entries.py`), keyboard shortcuts
  (`window_input.py`), and the button toolbar (`controls.py`) all consult it
  against `MainWindow.current_format()`. Covered by `tests/unit/test_commands.py`.
- `app/pdf/image_transform.py` — `rotate_image` / `flip_image`: Pillow-based
  in-place transforms for image documents, format-preserving, atomic write.
  Unit-tested in `tests/unit/test_image_transform.py`.
- `app/pdf/flipper.py` — `flip_page`: mirrors one PDF page (bakes any `/Rotate`
  into the content first so the flip matches what is displayed). Unit-tested in
  `tests/unit/test_flipper.py`. `app/gui/rotate_actions.py` dispatches PDF vs
  image per document.
- `app/pdf/merger.py` — `merged_output_path(folder)` classifies a folder and names
  its output; `merge_folder` branches to the PDF (`pypdf`) or text
  (`write_text_atomic`) path. Covered by `tests/unit/test_merger.py`.

Adding a future format (e.g. `.docx`) is one enum member plus a real render path
(fitz cannot open docx), a doc in `file_formats/`, then widening the `formats`
of the commands it supports.
