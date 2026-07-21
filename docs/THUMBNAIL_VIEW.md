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

## Commands while the grid is active

While the grid is showing, the palette follows the **selected thumbnail**, not
the underlying open document:

- **File commands act on the selection** — Copy file path / name / name
  without extension, Open containing folder, File information, Open with…,
  Print, Rename file…, Delete file…, Copy page text, Copy page as image (all
  sizes), and Delete saved text fields all target the orange-framed file. Page-based
  commands read the selection's **first page**, and the live pixel sizes in
  the Copy-page-as-image titles show the selection's first-page size.
- **Command visibility follows the selection's format** — select an image and
  the PDF-only commands disappear; select a text file and the image commands
  do.
- **Rename file…** renames the selected file (and its sidecar) in place and
  refreshes the grid with the new name selected; the open document stays
  open. Renaming the thumbnail of the open document itself reopens it under
  the new name and leaves the grid.
- **Delete file…** moves the selected file (and its sidecar) to the recycle
  bin and selects the nearest thumbnail (the next one, or the previous when
  the last file was deleted); the open document stays open. Deleting the
  thumbnail of the open document itself opens the nearest file in the folder
  and leaves the grid.
- **Delete saved text fields** deletes the selected file's JSON sidecar on
  disk; the open document's on-screen fields are untouched unless the
  selection *is* the open document.
- **Commands that need the loaded document are hidden** while the grid shows:
  Save / Save as, Close, Reload, page navigation, Zoom to fit / 100%, page
  edits (swap/delete/insert/extract/rotate/flip/move), search, edit-mode
  commands, Export to PDF, Copy current view, and GIF play/pause. Their
  keyboard shortcuts (Ctrl+S, Page Down, …) are inactive too. Leave the grid
  (Esc) and they return.
- **Always reachable**: Thumbnails view (toggle), Zoom in/out (thumbnail
  size), Next/Previous file in directory, Open…, and every settings command.

## Details and limits

- Previews are rendered once at a base resolution (longest side 512 px) and
  only rescaled as the size changes — resizing is instant, but thumbnails
  larger than 512 px look slightly soft.
- Previews always show the **first page** of a document, and reflect the file
  as it is **on disk** — unsaved changes in the open working copy are not shown.
- The grid lists the directory as it was when the view opened; reopen the view
  to pick up files added or removed since.
