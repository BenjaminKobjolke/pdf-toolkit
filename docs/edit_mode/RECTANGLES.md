# Rectangles

Placing and styling **filled rectangles** — solid color blocks for highlighting,
redaction-style boxes, or backgrounds. See [EDIT_MODE.md](EDIT_MODE.md) for turning
edit mode on, selection, deferred saving, the JSON sidecar, and export — all shared
with text and images. Stacking (what sits in front) is covered in
[LAYERING.md](LAYERING.md).

## Add

Click **Add rectangle** (or run **Add rectangle** from the palette). A placement
chooser asks where it lands — top-left, page centre, view centre, or a custom
click. A new rectangle appears at a default size in a soft yellow. New elements are
placed **on top** of everything already on the page.

## Resize

- **Drag a corner handle** to resize. Unlike images, a rectangle resizes **freely**
  — width and height change independently (no fixed aspect ratio). The opposite
  corner stays anchored.
- Set an exact size from the palette: **Rectangle: width…** and **Rectangle:
  height…** (in pixels).

## Move

- **Drag** the rectangle with the mouse.
- With it selected, **arrow keys** nudge it `10 px` at a time; **Shift + arrow**
  nudges `1 px`.

## Style

- **Rectangle: fill color…** (palette) opens the color picker. A rectangle is
  fill-only — it has a single solid color and no border.

## Delete

Press **Delete** / **Backspace** while the rectangle is selected, or run
**Rectangle: delete** from the palette.

## What the sidecar stores

Per rectangle: page index, position and size, fill color, and the stacking order
(`z`).
