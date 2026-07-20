# Thumbnails View

The GUI viewer can swap the page view for a **grid of first-page previews** of
every openable file in the current document's directory — a fast, keyboard-first
way to jump between the files of a folder.

## Opening and closing

Run **Thumbnails view** from the command palette (Ctrl+Shift+P). The command
needs an open document and toggles: running it again returns to the page view.

- The grid **replaces the page view in place** — the toolbar, status bar, menu
  bar, and the command palette all stay available while it is showing.
- **Esc** also leaves the grid and returns to the current document.
- Opening a file from anywhere else while the grid is showing (recent list,
  Open dialog, palette) closes the grid automatically, so it never covers a
  freshly opened document.

## What the grid shows

- Every **openable file** in the current document's folder — the same file set,
  ordering (case-insensitive alphabetical), and Open-dialog filter as
  **Next/Previous file in directory**. Files the viewer cannot render are not
  listed.
- Each cell is a **uniform square** preview of the file's first page,
  center-cropped, with the filename underneath. PDFs, images, and text/markdown
  documents all get real previews (they render through the same engine as the
  main view).
- Previews load **lazily**, one file per event-loop tick, starting at the
  selected file so what is on screen fills first. Until a preview is rendered,
  the cell shows a gray placeholder; a file that fails to render keeps the
  placeholder (and logs a warning) without stopping the rest.

## Navigation

| Key | Action |
|-----|--------|
| **Arrow keys** | Move the selection through the grid. |
| **Enter** | Open the selected file in the regular viewer (leaves the grid). |
| **Esc** | Return to the current document. |
| **Double-click** | Same as Enter. |

The **currently open file starts selected** and scrolled into view. The
selected thumbnail is marked with an **orange stroke** drawn around the preview
itself (not the filename); the stroke keeps a constant width at every
thumbnail size.

## Thumbnail size

While the grid is showing, the regular zoom commands are **redirected to the
thumbnail size** instead of the page zoom:

| Command / key | Effect |
|---------------|--------|
| **Zoom in 10%** (`Ctrl++`, `Ctrl+↑`) | Grow thumbnails 10%. |
| **Zoom out 10%** (`Ctrl+-`, `Ctrl+↓`) | Shrink thumbnails 10%. |

- Default **256×256 px**, clamped to **64–1024 px**.
- The size is **remembered across sessions** (stored in the sqlite settings
  backend; see `REMEMBERED_SETTINGS.md`). Reset it from **Remembered
  settings…** ("Thumbnail size").
- The page zoom of the underlying document is untouched; once you leave the
  grid, the zoom keys act on the page again. **Zoom to fit** and **Zoom 100%**
  are not redirected.

## Details and limits

- Previews are rendered once at a base resolution (longest side 512 px) and
  only rescaled as the size changes — resizing is instant, but thumbnails
  larger than 512 px look slightly soft.
- Previews always show the **first page** of a document, and reflect the file
  as it is **on disk** — unsaved changes in the open working copy are not shown.
- The grid lists the directory as it was when the view opened; reopen the view
  to pick up files added or removed since.
