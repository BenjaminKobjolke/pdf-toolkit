# File Formats (multi-format viewer)

The GUI viewer opens **PDF, plain-text (`.txt`), and Markdown (`.md`)** documents —
plus **any other plain-text file** (`.ini`, `.log`, `.json`, …) via a content sniff
(see *Opening a file*). Each command declares which formats it supports, so a
feature is reachable only for the formats it actually works on — you can read,
search, and open links in a `.txt` or `.md`, but page operations like *Delete page*
stay PDF-only.

`.md` files render as **formatted markdown** — `## x` becomes a heading, `**bold**`,
lists, code, and links are styled. Text (`.txt`/`.md`) documents are turned into a
styled HTML document and handed to fitz's HTML engine (fitz has no native markdown
reader). The **font size** and a **light/dark theme** are adjustable from the command
palette and remembered across sessions (see below).

## What works per format

| Feature | PDF | txt | md |
|---------|:---:|:---:|:--:|
| View / navigate / zoom | ✅ | ✅ | ✅ |
| Dark mode + font size (palette) | — | ✅ | ✅ |
| Formatted rendering (`##`→heading) | — | — | ✅ |
| Search text (`Ctrl+F`) | ✅ | ✅ | ✅ |
| Open / copy link (vim hints) | ✅ | ✅ | ✅ |
| Select mode (vim-style copy) | ✅ | ✅ | ✅ |
| Copy page text / file path / name | ✅ | ✅ | ✅ |
| Print, rename, open folder | ✅ | ✅ | ✅ |
| Delete / insert / extract / swap / rotate / move page | ✅ | — | — |
| Edit mode (text fields, images, rectangles), export | ✅ | — | — |
| Save / Save As | ✅ | — | — |
| Merge folder | ✅ (→ `merged.pdf`) | ✅ (→ `merged.txt`) | ✅ (→ `merged.md`) |

Commands that don't apply to the open document's format are greyed out in the
command palette and their keyboard shortcuts are no-ops. Format-agnostic commands
(Open, Exit, settings, toggles) are always available.

## Opening a file

- The **Open** dialog's filter is **user-configurable**: by default it lists
  `.pdf`, `.txt`, and `.md` files; **Open dialog: toggle all files** switches to
  listing everything, and **Open dialog: file extensions…** edits the extension
  list (e.g. `pdf, txt, md, ini`). Both persist across sessions and reset from
  **Remembered settings…** ("Open dialog filter").
- Passing a path on the command line — `pdft_gui.bat notes.md` — opens it directly.
- **Next / previous file in directory** (Alt+Right / Alt+Left) steps through the
  same filter's matches in the current document's folder, skipping files that
  fail the content sniff.
- **Unknown extensions are content-sniffed**: if the file's leading bytes are plain
  UTF-8 text (no null bytes), it opens as a `.txt`-style document — so `.ini`,
  `.log`, `.cfg`, `.json`, … just work. Binary or non-UTF-8 files are rejected
  with a warning rather than handed to the renderer to fail obscurely. A known
  suffix always wins — a `.pdf` is never sniffed.

## Merging text folders

*Merge folder…* now dispatches on the folder's contents:

- A folder of **PDFs / images** → `merged.pdf` (pages concatenated, as before).
- A folder of **text files** (`.txt` / `.md`) → `merged.<ext>`: the files are read
  as UTF-8 and concatenated (blank line between files). The output extension is the
  shared one when uniform (all `.md` → `merged.md`), otherwise `.txt`.
- A folder **mixing** text with PDF/image files is refused.

This applies to the CLI `pdf-merge-folder.bat` too — it shares the same backend.

## How it fits together

- `app/pdf/file_format.py` — the `FileFormat` enum (`.pdf` / `.txt` / `.md`),
  `FileFormat.of(path)` (suffix → format; an unknown suffix falls back to a content
  sniff — first 8KB, no null bytes, valid UTF-8 → `TXT` — else `None`), and
  `open_fitz(source)`. `open_fitz` is the single seam every fitz consumer uses; for
  text formats it builds a styled HTML document (via `app/pdf/text_html.py`) and opens
  it with `filetype="html"` — so `.md` renders formatted and `.txt`/`.md` honor the
  font-size / dark-mode preferences. `set_text_view_settings(...)` sets those (a
  module-level holder read at open time). Unit-tested in `tests/unit/test_file_format.py`.
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
  agnostic, `PDF_ONLY`, or `VIEWABLE` = pdf/txt/md) and a `available(fmt)` gate.
  The command palette (`palette_entries.py`), keyboard shortcuts
  (`window_input.py`), and the button toolbar (`controls.py`) all consult it
  against `MainWindow.current_format()`. Covered by `tests/unit/test_commands.py`.
- `app/pdf/merger.py` — `merged_output_path(folder)` classifies a folder and names
  its output; `merge_folder` branches to the PDF (`pypdf`) or text
  (`write_text_atomic`) path. Covered by `tests/unit/test_merger.py`.

Adding a future format (e.g. `.docx`) is one enum member plus a real render path
(fitz cannot open docx), then widening the `formats` of the commands it supports.
