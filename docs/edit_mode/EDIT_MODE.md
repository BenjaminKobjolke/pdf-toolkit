# Edit Mode

Edit mode lets you place **text fields** and **images** onto a PDF page, adjust
them, and bake them permanently into the file. This page is the overview; the
details live in two companion docs:

- [TEXT_EDITING.md](TEXT_EDITING.md) — placing and styling text fields.
- [IMAGE_EDITING.md](IMAGE_EDITING.md) — placing, scaling, and storing images
  (e.g. a transparent `signature.png`).

## Opening the viewer

```
pdft_gui.bat path\to\document.pdf
```

Or start the wizard (`pdft.bat`), choose **Open GUI viewer**, then
**File → Open PDF…**.

## Turning edit mode on

Editing is a toggle. Click **Edit mode** in the toolbar (or run **Toggle edit
mode** from the command palette) to reveal the styling controls and the **Add
field**, **Add image**, **Delete field**, and **Export** buttons.

Existing fields and images are **always shown** on the page, whether or not edit
mode is on. Edit mode only controls whether you can move, edit, scale, add, or
delete them — turn it off and they stay visible but become read-only. The status
bar reads **Edit Mode** while it is on, otherwise **Regular Mode** (see
`../STATUS_BAR.md`).

## Selecting elements

- **Click** an element to select it.
- **Tab** selects the next editable element on the page, **Shift+Tab** the
  previous one, cycling in reading order (top-to-bottom, then left-to-right). The
  palette commands **Select next / previous editable element** do the same (and
  turn edit mode on first).
- With something selected, **arrow keys** move it `10 px` at a time (`1 px` with
  **Shift**); **Delete** / **Backspace** removes it.

## Deferred saving and the JSON sidecar

Layout changes are **deferred**: they go to a temporary working copy and reach
the original PDF (and its JSON sidecar) only when you **Save** (`Ctrl+S`). The
footer shows **● Modified** until then. See the *Deferred saving* section of
`../COMMAND_PALETTE.md` for the full save/discard flow.

Configuration is written automatically to a JSON file named after the PDF:

```
document.pdf  ->  document.json
```

Autosave is debounced and writes to the **working copy's** sidecar; the original
`document.json` is updated (or removed, if you cleared everything) only on
**Save**. When you open a PDF with a matching `.json` sidecar, its fields and
images load automatically.

The sidecar is **version 2**: it stores text fields and images together (older
version-1 sidecars with text only still load). A malformed sidecar is reported
when the PDF is opened and otherwise ignored. See each companion doc for the
exact per-element fields.

## Exporting onto the PDF

Click **Export** (or run **Export to PDF (text + images)** from the palette) to
**flatten** all fields and images into the document — positions and sizes shown
in the viewer map 1:1 onto the result, and PNG transparency is preserved.

Exporting **commits straight to disk** (unlike the deferred layout edits) and
asks how:

- **Yes — overwrite the original.** The overlay is baked into the original file
  (a timestamped backup is written first) and the editable JSON sidecar is
  deleted. The elements are cleared from the view; they now live in the page and
  can no longer be edited.
- **No — export to a new file.** You are prompted for a name, pre-filled with the
  original. A flattened copy is written there while the **original PDF and its
  overlay stay untouched and editable**. The new file has no sidecar.
- **Cancel.** Nothing happens.
