# Text Editing

The GUI viewer can place text fields onto a PDF page, style them, and write them
permanently into the file. Field layouts are saved alongside the PDF as a JSON
sidecar and reloaded automatically the next time you open that PDF.

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

Field configuration is written automatically to a JSON file next to the PDF, named
after it:

```
document.pdf  ->  document.json
```

Saving is debounced — it happens shortly after you stop editing, and again on
export. When you open a PDF that has a matching `.json` sidecar, its fields are
loaded automatically (toggle **Edit text** to see and adjust them).

The sidecar stores, per field: page index, position and size, the text, font
family/size, text colour, background colour (or `null` for transparent), and the
bold/italic flags. A malformed sidecar is reported when the PDF is opened and is
otherwise ignored.

## Exporting onto the PDF

Click **Export text** to write all fields onto the PDF. Export writes a **new
file** next to the original, with `_text-embedded` inserted before the extension,
and leaves the source PDF untouched:

```
document.pdf  ->  document_text-embedded.pdf
```

Re-exporting overwrites the `_text-embedded` copy. Export draws the text (and any
background rectangles) directly onto each page; positions and sizes shown in the
viewer map 1:1 onto the exported PDF.

## Fonts

Any installed system font can be selected. When exporting, the chosen font file is
embedded into the PDF so the text renders the same elsewhere. If a specific font
file cannot be resolved or embedded — including a bold/italic variant that has no
dedicated file — the export falls back to a standard built-in font (Helvetica and
its bold/italic/bold-italic variants). Export does not fail because of a font; it
substitutes and continues.

## Notes and limitations

- Fitz (PyMuPDF) performs the text writing; the page-reordering operations
  (swap/delete/merge) continue to use pypdf.
- Bold/italic are not synthesised on embedded fonts — a real style file is used
  when available, otherwise a styled built-in font.
- After export, the on-screen page is not re-rendered; the live field items
  already match what was written to the file.
