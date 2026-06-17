# Keyboard and Mouse Controls

The GUI viewer (`pdft-gui`) is keyboard-first. Common actions have direct keys;
everything else is reachable through the command palette. The keys below are the
**built-in defaults** (registered in `app/gui/window_input.py` — `_SHORTCUTS` +
`_PALETTE_CHORD`); mouse gestures live in `_MOUSE_CONTROLS`. Press **F1** in the
viewer to see the current list in a searchable dialog.

Every shortcut here can be **changed, added, or removed** at runtime — see
`CONFIGURE_SHORTCUTS.md`. The command palette shows each command's current chord
right-aligned.

## Palette & search

| Key | Action |
|-----|--------|
| **Ctrl+Shift+P** | Open the command palette |
| **F1** | Show keyboard and mouse controls |
| **Ctrl+F** | Search PDF text |
| **Ctrl+Shift+F** | Search text fields |
| **Ctrl+Shift+H** | Clear search highlights |

## Page edits & saving

| Key | Action |
|-----|--------|
| **Ctrl+R** | Rotate current page 90° right |
| **Ctrl+Shift+R** | Rotate current page 90° left |
| **Ctrl+S** | Save changes to the original file |

Page edits (rotate, move, delete, swap) and text edits go to a temporary working
copy first; the original file changes only when you **Save** (Ctrl+S). Closing
the window with unsaved changes prompts to Save, Discard, or Cancel. Moving a
page (to next/previous/first/last) is palette-only; see `COMMAND_PALETTE.md`.

## Navigation

| Key | Action |
|-----|--------|
| **Page Down** | Next page |
| **Page Up** | Previous page |
| **Home** | First page |
| **End** | Last page |

## Zoom

| Key | Action |
|-----|--------|
| **Ctrl++** / **Ctrl+=** / **Ctrl+↑** | Zoom in 10% |
| **Ctrl+-** / **Ctrl+↓** | Zoom out 10% |
| **Ctrl+0** | Zoom 100% |

Zoom level persists as you move between pages. **Zoom to fit** is available from
the palette (no default key).

## Edit mode (text fields & images)

These act on the page overlay while edit mode is on; see
`edit_mode/EDIT_MODE.md`.

| Key | Action |
|-----|--------|
| **Tab** / **Shift+Tab** | Select next / previous editable element (reading order) |
| **Arrow keys** | Move the selected element 10 px (**Shift+Arrow** = 1 px) |
| **+** / **-** | Scale the selected image (about its center, aspect locked) |
| **Ctrl+↑** / **Ctrl+↓** | Selected text field: font size · selected image: scale · else: zoom page |
| **Enter** | Edit the selected text field |
| **Delete** / **Backspace** | Delete the selected element |

## Mouse

| Gesture | Action |
|---------|--------|
| **Wheel** | Scroll the page; flip to the next/previous page at the scroll edge |
| **Shift+Wheel** | Scroll horizontally |
| **Ctrl+Wheel** | Previous / next page (regardless of scroll position) |

Shortcuts that act on a document (navigation, zoom) are no-ops until a PDF is
open. The remaining viewer commands — page edits, text/image editing, document
management, and the palette appearance settings — live in the command palette;
see `COMMAND_PALETTE.md`.
