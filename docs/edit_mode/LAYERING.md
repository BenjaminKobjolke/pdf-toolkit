# Layering

Overlapping elements have a **stacking order**: the one in front hides the ones
behind it, both on screen and in the exported PDF. Layering works across **all
element types together** — a rectangle, an image, and a text field share one order,
so any element can sit above or below any other.

See [EDIT_MODE.md](EDIT_MODE.md) for turning edit mode on and selecting elements.

## Reorder the selected element

Select an element, then:

| Action | Shortcut | Palette command |
| --- | --- | --- |
| Move forward (up one) | **Ctrl+]** | **Layer: move forward** |
| Move backward (down one) | **Ctrl+[** | **Layer: move backward** |
| Bring to front | **Ctrl+Shift+]** | **Layer: bring to front** |
| Send to back | **Ctrl+Shift+[** | **Layer: send to back** |

**Move forward / backward** swap the element with its immediate neighbour;
**bring to front / send to back** jump it past everything else. A newly added
element always starts at the front.

The shortcuts are rebindable like any other — see `../COMMAND_PALETTE.md`.

## How it is saved and exported

Each element stores its stacking order (`z`) in the JSON sidecar (version 3), so
the order survives save/reload. On **Export**, elements are flattened
back-to-front in that same order, so the printed result matches the screen.

Sidecars from older versions (which had no stacking order) load with images kept
above text — their original appearance — and gain an explicit order on the next
save.
