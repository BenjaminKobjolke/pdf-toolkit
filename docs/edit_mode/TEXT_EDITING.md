# Text Editing

Placing and styling **text fields**. See [EDIT_MODE.md](EDIT_MODE.md) for turning
edit mode on, selection (Tab/Shift+Tab), deferred saving, the JSON sidecar, and
export — all shared with images.

## Add

Click **Add field** (or **Add text field** in the palette). A placement chooser
asks where the field lands — top-left, page centre, view centre, or a custom
click. A new field appears using the current font/size/colour settings.

## Edit the text

Double-click a field to type into it, or select it and press **Enter** (also
**Field: change text…** in the palette). Click elsewhere to finish editing. While
typing, the arrow keys move the text cursor (not the field).

## Move

- **Drag** a field with the mouse.
- With a field selected, **arrow keys** nudge it `10 px` at a time; **Shift +
  arrow** nudges `1 px` for fine alignment.
- **Ctrl + ↑ / ↓** grows / shrinks the selected field's **font size**.

## Style

Select a field, then adjust the controls (they apply to the selected field and
become the defaults for the next field you add):

- **Font** — any font installed on your system.
- **Size** — point/pixel size of the text.
- **B** / **I** — bold and italic toggles.
- **Text colour…** — a colour picker for the glyph colour.
- **Background** — a toggle; off means a transparent background (default). Turn it
  on to pick a fill colour drawn behind the text.

All of these are also available from the palette (**Field: font size…**,
**Field: font family…**, **Field: text colour…**, **Field: background colour…**,
**Field: toggle bold / italic**) when a field is selected.

## Delete

Click **Delete field**, or press **Delete** / **Backspace** while a field is
selected (not while typing inside it).

## What the sidecar stores

Per text field: page index, position and size, the text, font family/size, text
colour, background colour (or `null` for transparent), and the bold/italic flags.

## Fonts

Any installed system font can be selected. When exporting, the chosen font file
is embedded into the PDF so the text renders the same elsewhere. If a font file
cannot be resolved or embedded — including a bold/italic variant with no
dedicated file — export falls back to a standard built-in font (Helvetica and its
bold/italic/bold-italic variants). Export never fails because of a font; it
substitutes and continues. Bold/italic are not synthesised on embedded fonts — a
real style file is used when available, otherwise a styled built-in font.
