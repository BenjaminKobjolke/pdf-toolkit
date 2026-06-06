# Keyboard Shortcuts

The GUI viewer (`pdft-gui`) is keyboard-first. Common actions have direct keys;
everything else is reachable through the command palette. The keys below are
registered in `app/gui/window_input.py` (`_SHORTCUTS` + `_PALETTE_CHORD`). Press
**F1** in the viewer to see this list in a searchable dialog.

## Palette & search

| Key | Action |
|-----|--------|
| **Ctrl+Shift+P** | Open the command palette |
| **F1** | Show keyboard shortcuts |
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

Shortcuts that act on a document (navigation, zoom) are no-ops until a PDF is
open. The remaining viewer commands — page edits, text editing, document
management, and the palette appearance settings — live in the command palette;
see `COMMAND_PALETTE.md`.
