# Text Editing

The GUI viewer can place text fields onto a PDF page, style them, and bake them
permanently into the file. Field layout changes are **deferred**: they go to a
temporary working copy and reach the original PDF (and its JSON sidecar) only
when you **Save** (`Ctrl+S`). The saved layout is reloaded automatically the next
time you open that PDF. **Export text to PDF** is different — it commits straight
to disk (see *Exporting onto the PDF* below). See the *Deferred saving* section
of `COMMAND_PALETTE.md` for the full save/discard flow.

## Opening the viewer

Launch the GUI on a file:

```
pdft_gui.bat path\to\document.pdf
```

Or start the wizard (`pdft.bat`) and choose **Open GUI viewer**, then use
**File → Open PDF…**.

## Entering edit mode

Text editing is a toggle. Click **Edit text** in the toolbar to reveal the styling
controls and the **Add field**, **Delete field**, and **Export text** buttons.

Existing text fields are **always shown** on the page, whether or not edit mode is
on. Edit mode only controls whether you can move, edit, add, or delete them — turn
it off and the fields stay visible but become read-only.

## Working with text fields

### Add

Click **Add field**. A new field appears near the top-left of the page using the
current font/size/colour settings.

### Edit the text

Double-click a field to type into it. Click elsewhere (or press the field's focus
away) to finish editing.

### Move

- **Drag** a field with the mouse to position it anywhere on the page.
- With a field selected, use the **arrow keys** to nudge it `10 px` at a time.
- Hold **Shift + arrow** to nudge it `1 px` at a time for fine alignment.

Arrow keys move the field only when it is selected and *not* being text-edited
(while typing, the arrows move the text cursor as usual).

### Style

Select a field, then adjust the controls; changes apply to the selected field and
become the defaults for the next field you add:

- **Font** — any font installed on your system (`QFontComboBox`).
- **Size** — point/pixel size of the text.
- **B** / **I** — bold and italic toggles.
- **Text colour…** — opens a colour picker for the glyph colour.
- **Background** — a toggle button. Off means a transparent background (the
  default). Turn it on to pick a fill colour drawn behind the text.

### Delete

- Click **Delete field** to remove the selected field(s), or
- press **Delete** / **Backspace** while a field is selected (this does not delete
  while you are typing inside a field).

## Saving the layout (JSON sidecar)

Field configuration is written automatically to a JSON file named after the PDF:

```
document.pdf  ->  document.json
```

Autosave is debounced — it happens shortly after you stop editing — but it writes
to the **working copy's** sidecar, not the original. The original `document.json`
is updated (or removed, if you cleared every field) only when you **Save**
(`Ctrl+S`); the footer shows **● Modified** until then. When you open a PDF that
has a matching `.json` sidecar, its fields are loaded automatically (toggle
**Edit text** to see and adjust them).

The sidecar stores, per field: page index, position and size, the text, font
family/size, text colour, background colour (or `null` for transparent), and the
bold/italic flags. A malformed sidecar is reported when the PDF is opened and is
otherwise ignored.

## Exporting onto the PDF

Click **Export text** (or run **Export text to PDF** from the palette) to **flatten**
all fields into the document. The text (and any background rectangles) is drawn
directly onto each page — positions and sizes shown in the viewer map 1:1 onto the
result.

Unlike the deferred layout edits, exporting **commits straight to disk** and asks
how:

- **Yes — overwrite the original.** The text is baked into the original file (a
  timestamped backup is written first, as with every save) and the editable JSON
  sidecar is deleted. The fields are cleared from the view; the text now lives in
  the page and can no longer be edited.
- **No — export to a new file.** You are prompted for a file name, pre-filled with
  the original name and the caret at the end. A flattened copy is written there
  while the **original PDF and its fields stay untouched and editable**. The new
  file has no sidecar.
- **Cancel.** Nothing happens; the fields stay in place.

## Fonts

Any installed system font can be selected. When exporting, the chosen font file is
embedded into the PDF so the text renders the same elsewhere. If a specific font
file cannot be resolved or embedded — including a bold/italic variant that has no
dedicated file — the export falls back to a standard built-in font (Helvetica and
its bold/italic/bold-italic variants). Export does not fail because of a font; it
substitutes and continues.

## Notes and limitations

- Fitz (PyMuPDF) performs the text writing; the page operations (rotate, move,
  swap, delete, merge) use pypdf.
- Bold/italic are not synthesised on embedded fonts — a real style file is used
  when available, otherwise a styled built-in font.
- After an **overwrite** export the page is re-rendered with the baked-in text and
  the editable field items are removed (the text now lives in the page itself). A
  **new-file** export leaves the on-screen fields untouched so you can keep editing.
