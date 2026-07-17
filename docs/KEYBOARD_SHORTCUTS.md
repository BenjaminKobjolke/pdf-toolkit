# Keyboard and Mouse Controls

The GUI viewer (`pdft-gui`) is keyboard-first. Common actions have direct keys;
everything else is reachable through the command palette. The keys below are the
**built-in defaults** (registered in `app/gui/window_input.py` — `_SHORTCUTS` +
`_PALETTE_CHORD`); mouse gestures live in `_MOUSE_CONTROLS`. Press **F1** in the
viewer to open a chooser: **Keyboard shortcuts…** opens the editable dialog
(Enter binds a chord; binding to an action that already has shortcuts asks
whether to **Add** the new chord or **Replace** the existing one(s); **Del
deletes a shortcut** — for an action with several chords it lets you pick **All
shortcuts** or one specific chord), and **Mouse controls** opens the read-only
list of wheel gestures. An action can hold **multiple chords**, and every row
lists all of them.

Every shortcut here can be **changed, added, or removed** at runtime — see
`CONFIGURE_SHORTCUTS.md`. The command palette shows each command's current chord
right-aligned.

## Palette & search

| Key | Action |
|-----|--------|
| **Ctrl+Shift+P** | Open the command palette |
| **F1** | Choose keyboard shortcuts (editable) or mouse controls |
| **Ctrl+F** | Search document text |
| **Ctrl+Shift+F** | Search text fields |
| **Ctrl+Shift+H** | Clear search highlights |
| **Esc** | Clear the active search highlight (when not in select mode) |

After a **Search document text** match, opening **select mode** (`Ctrl+Shift+S`) starts
its cursor on the matched word. **Copy all text from current page** (palette) copies
the whole page to the clipboard. See `SELECT_MODE.md`.

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
| **Alt+Right** | Next file in directory |
| **Alt+Left** | Previous file in directory |

**Next / previous file in directory** steps alphabetically through the openable
files beside the current document (wrapping at the ends). It honors the
Open-dialog filter, skips files the viewer can't render, and prompts to save
unsaved changes before switching.

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

## Select mode (vim-style text copy)

Read-only mode for copying the PDF's own text with the keyboard. Toggle it, then
hop word to word, select with **v**, and copy with **y**. Full reference:
`SELECT_MODE.md`.

| Key | Action |
|-----|--------|
| **Ctrl+Shift+S** | Toggle text select mode |
| **h** / **l** / **←** / **→** (or **b** / **w**) | Previous / next word |
| **j** / **k** / **↓** / **↑** | Down / up one line |
| **0** / **$** | First / last word of the line |
| **gg** / **G** | First / last word of the page |
| **v** | Start / cancel a visual selection |
| **y** | Copy the selection (or current word) to the clipboard |
| **Esc** / **q** | Leave select mode |

## Open / Copy link (vim-style link hints)

Label every link on the current page, then **Open link** (browser) or **Copy
link** (clipboard) by keyboard. Palette-only by default (no built-in chord;
bindable via **Configure keyboard shortcuts…**). Full reference: `OPEN_LINK.md`.

| Key | Action |
|-----|--------|
| **a**, **b**, **c**, … | Open/copy the link with that label (`aa`, `ab`, … past 26) |
| **Esc** | Leave the mode |

## File browser (open / save / folder)

Choosing a file or folder (open, insert, add image, save-as, extract, merge)
opens a custom keyboard-first browser instead of the OS dialog. Full reference:
`FILE_BROWSER.md`.

| Key | Action |
|-----|--------|
| **j** / **k** / **↓** / **↑** | Move down / up one entry |
| **gg** / **G** | First / last entry |
| **l** / **→** / **Enter** | Enter folder, or pick the file |
| **h** / **←** / **Alt+↑** (or the `..` row) | Up one level (drive list at a drive root) |
| **/** | Type-ahead filter |
| **Tab** | (save) jump to the filename field |
| **Esc** / **q** | Cancel |

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
