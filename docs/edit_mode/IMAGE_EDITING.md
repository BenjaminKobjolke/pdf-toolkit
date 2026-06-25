# Image Editing

Placing, scaling, and storing **images** — for example a signature with a
transparent background. See [EDIT_MODE.md](EDIT_MODE.md) for turning edit mode on,
selection (Tab/Shift+Tab), deferred saving, the JSON sidecar, and export — all
shared with text fields.

## Add

Use **Add image** (toolbar) or **Add image…** (palette). You are asked two things:

- **Where to store it:**
  - **Copy into `assets/`** — a copy is placed in an `assets/` folder next to the
    PDF and stored as the relative path `assets/<name>`. This keeps the document
    self-contained (move the PDF + its `assets/` folder together). Name collisions
    get a numeric suffix (`sig_1.png`).
  - **Reference the original** — the image is left where it is and stored as its
    absolute path. Nothing is copied.
  - The last choice is remembered and pre-selected next time; reset it from
    **Remembered settings…** in the palette.
- **Where to place it** on the page — top-left, page centre, view centre, or a
  custom click (the same chooser as text fields).

Asset paths always resolve against the **original PDF's directory**, both on
screen and when the overlay is flattened.

## Move

- **Drag** the image with the mouse.
- With the image selected, **arrow keys** nudge it `10 px` at a time (`1 px` with
  **Shift**).

## Scale

Scaling is always **aspect-ratio locked**, so signatures and logos never distort.

- **Corner handles** — drag any corner of the selected image; the opposite corner
  stays anchored.
- **Keyboard** — **+** / **-**, or **Ctrl + ↑ / ↓**, grow / shrink the selected
  image **about its center** (it stays in place). *(When an image is selected,
  `Ctrl+↑/↓` scales it instead of zooming the page — deselect to zoom.)*
- **Palette** — **Image: scale…** prompts for an exact factor (× of the original
  size), also center-anchored.

## Delete

**Delete** / **Backspace** while the image is selected, or **Image: delete** from
the palette.

## Transparency

PNG alpha is preserved both on screen and when the overlay is flattened onto the
PDF, so a transparent-background signature stays transparent.

## What the sidecar stores

Per image: page index, position and on-page size, the path (`assets/<name>` when
copied, or an absolute path when referenced), whether the path is absolute, the
opacity, and the stacking order (`z`).

## Asset folder layout

```
my-folder/
  contract.pdf
  contract.json        # sidecar (text + images)
  assets/
    signature.png      # copied images live here
```

Referenced (not copied) images stay at their original absolute location and are
not placed under `assets/`.
