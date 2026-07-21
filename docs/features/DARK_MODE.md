# Dark mode (text & Markdown)

The viewer can render **plain-text (`.txt`) and Markdown (`.md`)** documents in a
**light** or **dark** reading theme. Dark mode is light-on-dark (`#dddddd` text on a
`#1e1e1e` background), easier on the eyes for long reading.

Dark mode applies to **text formats only**. PDFs keep their own colors and are not
affected.

## Toggling it

Open the command palette (**Ctrl+Shift+P**) with a `.txt` or `.md` file open and run:

| Command | Effect |
|---------|--------|
| **Text/Markdown: toggle dark mode** | Flip light ⇄ dark. |
| **Text/Markdown: font size…** | Set the base font size (6–40 pt). |

Both commands are **shown only when a text/markdown document is open** — they are hidden
(and their shortcuts are no-ops) for PDFs, since the theme has no meaning there.

You can also bind them to keyboard shortcuts via **Configure keyboard shortcuts…** (see
`../CONFIGURE_SHORTCUTS.md`).

## What it changes

Text and Markdown documents render through an HTML engine, and dark mode swaps the CSS
palette used to draw them:

| | Foreground | Background | Links |
|--|-----------|-----------|-------|
| **Light** (default) | `#000000` | `#ffffff` | `#0645ad` |
| **Dark** | `#dddddd` | `#1e1e1e` | `#6cb6ff` |

For `.md` this is applied on top of the formatted rendering (`##` → heading, `**bold**`,
lists, code, links). See `../file_formats/TEXT.md`.

## Persistence

The theme choice and font size are **remembered across sessions** — stored in the sqlite
settings backend under **"Text/Markdown appearance"**. Restored on the next launch and on
every text/markdown file you open.

Reset them (individually or with everything else) via the palette command
**Remembered settings…** (see `../REMEMBERED_SETTINGS.md`).

## How it fits together

- `app/config/text_view_settings.py` — `TextViewSettings` (`font_pt`, `dark_mode`) and its
  persisted store.
- `app/pdf/text_html.py` — builds the themed HTML/CSS from the document text (light/dark
  palettes are the constants at the top of the module).
- `app/pdf/file_format.py` — `open_fitz` reads the active settings and renders text formats
  as that HTML; `set_text_view_settings(...)` updates them.
- `app/gui/text_view_controller.py` — the palette commands: edit → persist → reload.

Covered by `tests/unit/test_text_html.py`, `tests/unit/test_text_view_settings.py`, and
`tests/unit/test_file_format.py`.
