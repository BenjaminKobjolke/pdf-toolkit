# Text (`.txt`) and Markdown (`.md`)

Text documents are turned into a styled HTML document and handed to fitz's
HTML engine (fitz has no native markdown reader) — see `render_html` in
`app/pdf/text_html.py` and the `open_fitz` seam in `app/pdf/file_format.py`.

- `.md` renders as **formatted markdown** — `## x` becomes a heading,
  `**bold**`, lists, code, and links are styled (the `markdown` package).
- `.txt` renders as plain preformatted text.
- **Any other plain-text file** (`.ini`, `.log`, `.json`, …) opens the same
  way via the content sniff — first 8 KB must be valid UTF-8 with no null
  bytes (see *Opening a file* in `../FILE_FORMATS.md`). Binary or non-UTF-8
  files are rejected with a warning. A known suffix always wins — a `.pdf` is
  never sniffed.

## Appearance (palette, only shown for text formats)

Both persist across sessions; reset from **Remembered settings…**
("Text/Markdown appearance"). Changing the font size re-paginates.

| Command | Range | Effect |
|---------|-------|--------|
| **Text/Markdown: toggle dark mode** | — | Light ⇄ dark reading theme. |
| **Text/Markdown: font size…** | 6–40 pt | Base font size. |

## What works

Read, search, open/copy links (bare `http(s)://` URLs in the text), select
mode, copy page text, print, copy as image. Text documents are read-only —
no page operations, no rotate/flip, no save. Full comparison: capability
table in `../FILE_FORMATS.md`.

**Merge folder** on a folder of text files concatenates them to
`merged.txt` / `merged.md` (see *Merging text folders* in
`../FILE_FORMATS.md`).
