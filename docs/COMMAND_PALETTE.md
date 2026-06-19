# Command Palette

The GUI viewer has a searchable command palette that exposes every viewer action
in one place — page operations, zoom, navigation, text editing, and document
management. It is the fastest way to reach a command without hunting through the
toolbar or menus.

## Opening the palette

Press **Ctrl+Shift+P** anywhere in the viewer, or use **File → Command palette…**.

> The top **menu bar is hidden by default** — the palette (Ctrl+Shift+P) is the
> primary entry point. Run **Toggle menu bar** to show it; the choice is
> remembered and restored next launch.

A filter box opens over a command list:

- **Type** to filter commands by name. Matching is **relaxed**: each
  whitespace-separated word must appear, in any order — `field del` finds
  **Field: delete**.
- **Up / Down** move the selection (wrapping at the ends).
- **Enter** runs the highlighted command.
- **Esc** closes the palette without running anything.

Commands that need an open document (zoom, navigation, page edits, text edits)
are hidden until a PDF is open.

### Recently-used ordering

The palette floats **recently-run commands to the top**, most-recent first, and
the single top-most command is shown in **bold** as the "last command" cue. The
order survives restarts — it is persisted in a global file:

```
~/.pdf-toolkit/command_history.json
```

The most-recent 50 command ids are kept (dedup + move-to-front). The location can
be overridden with the `PDF_TOOLKIT_COMMAND_HISTORY_FILE` environment variable; a
missing or corrupt file just means no commands are floated yet.

## Commands

| Command | What it does |
|---------|--------------|
| **Open PDF…** | Prompt for a PDF and open it. |
| **Open from recent / history…** | Pick from recently opened documents (see below). |
| **Save changes to original file** | Write the working copy back to the original (with a backup). See *Deferred saving*. |
| **Rename file…** | Rename the open PDF (and its sidecar) and reopen it. |
| **Close current document** | Offer to save unsaved changes, then return to the empty viewer. |
| **Toggle menu bar** | Show/hide the top menu bar (remembered across sessions). |
| **Toggle toolbar** | Show/hide the button toolbars (remembered across sessions). |
| **Toggle status bar** | Show/hide the footer status bar (remembered across sessions; see `STATUS_BAR.md`). |
| **Toggle fullscreen** | Enter/leave fullscreen for the current session (not remembered). |
| **Palette: width %…** | Set the palette width as a % of the window (see *Appearance settings*). |
| **Palette: height %…** | Set the palette height as a % of the window. |
| **Palette: font size…** | Set the palette font size in points (0 = default). |
| **Palette: opacity %…** | Set the palette window opacity. |
| **Palette: toggle borderless** | Show/hide the palette window frame. |
| **Outline: width…** | Stroke width (px) of the selected-element outline (see *Appearance settings*). |
| **Outline: type…** | Line type of the outline — Dashed or Solid. |
| **Outline: colour…** | Colour of the outline (keyboard-first picker). |
| **Exit** | Close the viewer. |
| **Show keyboard and mouse controls** | Open a searchable, read-only list of every key + mouse gesture (also **F1**). |
| **Previous page** / **Next page** | Step one page back / forward. |
| **First page** / **Last page** | Jump to the first / last page. |
| **Zoom to fit** | Scale the page to fit the window. |
| **Zoom 100%** | Show the page at true PDF size. |
| **Zoom in 10%** / **Zoom out 10%** | Scale up / down by 10%. |
| **Swap 2 pages** | Swap the two pages of a 2-page PDF. |
| **Delete current page** | Delete the page on screen (asks first). |
| **Delete page range…** | Delete an inclusive range of pages. |
| **Rotate page 90° left** / **90° right** / **180°** | Rotate the current page (also `Ctrl+Shift+R` / `Ctrl+R`). |
| **Move page to next position** / **previous position** | Swap the current page one step forward / back. |
| **Move page to first** / **to last** | Move the current page to the start / end. |
| **Merge folder…** | Merge a folder of PDFs and images into `merged.pdf`. |
| **Toggle edit mode** | Turn edit mode on / off (see `edit_mode/EDIT_MODE.md`). |
| **Select next / previous editable element** | Cycle selection through text fields and images (also **Tab** / **Shift+Tab**). |
| **Add text field** | Add a new text field (edit mode only). |
| **Add image…** | Place an image — e.g. a signature — on the page (edit mode only). |
| **Image: scale…** / **Image: delete** | Resize or remove the selected image. |
| **Delete selected field** | Remove the selected text field(s) (edit mode only). |
| **Export to PDF (text + images)** | Flatten the placed overlay into the document (deferred until save). |
| **Delete saved text fields for this document** | Delete this PDF's saved fields and its JSON sidecar. |
| **Configure keyboard shortcuts…** | Bind, rebind, or clear a command's keyboard shortcut (see `CONFIGURE_SHORTCUTS.md`). |
| **Set as default PDF viewer…** | Register the viewer as a Windows PDF handler, then open Default Apps (Windows only; see `DEFAULT_PDF_VIEWER.md`). |
| **Remove as PDF handler** | Undo the PDF-handler registration (Windows only; see `DEFAULT_PDF_VIEWER.md`). |
| **Remembered settings…** | Reset stored preferences (placement, image choice, palette, outline, keyboard shortcuts, …) individually or all. |
| **Search PDF text…** | Live full-text search of the document (see below). |
| **Search text fields…** | Live search of your placed text fields (see below). |
| **Clear search highlights** | Remove the gold match highlights (shown only while highlights exist). |

When a text field is **selected**, these extra commands appear in the palette
(and only then):

| Command | What it does |
|---------|--------------|
| **Field: change text…** | Edit the selected field's text. |
| **Field: font size…** | Type a new point/pixel size. |
| **Field: font family…** | Searchable list of installed fonts. |
| **Field: text colour…** | Keyboard-first colour picker (see below). |
| **Field: background colour…** | Same picker for the field's fill. |
| **Field: toggle bold** / **toggle italic** | Flip the style. |
| **Field: delete** | Remove the selected field. |

When an **image** is selected, these extra commands appear instead:

| Command | What it does |
|---------|--------------|
| **Image: scale…** | Type a new uniform scale factor (aspect ratio is locked). |
| **Image: delete** | Remove the selected image. |

You can also resize a selected image by dragging its corner handles, and grow /
shrink it with **+** / **-** (or **Ctrl+↑/↓**). See `edit_mode/IMAGE_EDITING.md`
for the full image workflow.

## Deferred saving

Page edits (rotate, move, delete, swap), **Export text to PDF**, and your text-field
layout all apply to a **temporary working copy** — the original file and its JSON
sidecar on disk are left untouched. The footer shows **● Modified** while there are
unsaved changes.

- **Save changes to original file** (`Ctrl+S`) writes the working copy back to the
  original, creating one timestamped backup (`backup/YYYYMMDD-HHMM-<name>.pdf`).
- Closing the window, opening another PDF, or closing the document while modified
  prompts to **Save**, **Discard**, or **Cancel**.

## Keyboard shortcuts

Common commands also have direct keys, so you do not have to open the palette:

| Key | Command |
|-----|---------|
| **Ctrl+Shift+P** | Open the command palette |
| **F1** | Show keyboard and mouse controls |
| **Ctrl+F** | Search PDF text |
| **Ctrl+Shift+F** | Search text fields |
| **Ctrl+Shift+H** | Clear search highlights |
| **Page Down** / **Page Up** | Next / previous page |
| **Home** / **End** | First / last page |
| **Ctrl++** (or **Ctrl+=**, **Ctrl+↑**) | Zoom in 10% |
| **Ctrl+-** (or **Ctrl+↓**) | Zoom out 10% |
| **Ctrl+0** | Zoom 100% |
| **Ctrl+R** / **Ctrl+Shift+R** | Rotate current page right / left |
| **Ctrl+S** | Save changes to the original file |
| **Tab** / **Shift+Tab** | Select next / previous editable element (edit mode) |
| **Ctrl+↑/↓** | Selected text field: font size · image: scale · else: zoom |
| **+** / **-** | Scale the selected image |
| **Wheel** | Scroll the page; flip page at the scroll edge |
| **Shift+Wheel** | Scroll horizontally |
| **Ctrl+Wheel** | Previous / next page |

Zoom level persists as you change pages. **Zoom to fit** is available from the
palette. The full key + mouse map lives in `KEYBOARD_SHORTCUTS.md`.

These keys are the built-in defaults — each command's current chord is shown
right-aligned in the palette, and all of them can be rebound, added, or cleared
via **Configure keyboard shortcuts…** (see `CONFIGURE_SHORTCUTS.md`).

## Appearance settings

The palette window itself is tunable, all from inside the palette (per-value
prompts) and remembered across sessions:

| Command | Range | Effect |
|---------|-------|--------|
| **Palette: width %…** | 20–100 | Width as a percentage of the main window. |
| **Palette: height %…** | 20–100 | Height as a percentage of the main window. |
| **Palette: font size…** | 0–40 pt | Font size of the filter box + list (0 keeps the default). |
| **Palette: opacity %…** | 20–100 | Window transparency. |
| **Palette: toggle borderless** | — | Removes/restores the OS window frame. |

Settings persist in a global file:

```
~/.pdf-toolkit/palette.json
```

The location can be overridden with the `PDF_TOOLKIT_PALETTE_FILE` environment
variable. A missing or corrupt file falls back to the defaults (width 80%,
height 60%, default font, opaque, framed).

### Selected-element outline

The dashed rectangle drawn around the **selected** text field or image in edit
mode is also tunable from the palette and remembered across sessions:

| Command | Range | Effect |
|---------|-------|--------|
| **Outline: width…** | 1–12 px | Stroke width of the outline (zoom-independent). |
| **Outline: type…** | Dashed / Solid | Line style of the outline. |
| **Outline: colour…** | any colour | Outline colour (same picker as the field colours). |

Settings persist in `~/.pdf-toolkit/outline.json` (override:
`PDF_TOOLKIT_OUTLINE_FILE`). A missing or corrupt file falls back to the default
**2 px dashed red (`#FF0000`)** — chosen to stand out more than Qt's faint
built-in selection marquee. Reset it from **Remembered settings…**.

## Search

Both searches are **live**: type at least **3 characters** and results refresh on
every keystroke. Navigate with the arrow keys, **Enter** to act, **Esc** to close.

- **Search PDF text…** (`Ctrl+F`) lists **one row per match** — `Page N: …text…`.
  Selecting a match jumps to its page and draws a **gold highlight** around it.
  Highlights stay until you run **Clear search highlights** (`Ctrl+Shift+H`).
- **Search text fields…** (`Ctrl+Shift+F`) searches the text you placed via the
  editor. Selecting a result jumps to that page and **selects** the field (edit
  mode turns on) — its field commands then appear in the palette.

## Colour picker

The colour commands open a keyboard-first picker:

- Type a **hex** value (`#ff8800`) or a **colour name** (`white`, `black`, `red`,
  …) in the box.
- A **preview swatch** updates live as you type or move through the list.
- Recently used colours appear at the top, followed by common names.
- **Enter** accepts the typed value or the highlighted row; **Esc** cancels.

No new dependency — the picker is the same searchable dialog used elsewhere.

## Open from recent / history

The viewer records every PDF you open (most recent first, up to 100 entries) in a
global file:

```
~/.pdf-toolkit/recent.json
```

**Open from recent / history…** shows that list — filename plus full path — in the
same type-to-filter dialog as the palette. Filter, select with the arrow keys, and
press **Enter** to open. The location can be overridden with the
`PDF_TOOLKIT_RECENT_FILE` environment variable.

## Remembered window state

Beyond the palette appearance and chrome toggles above, the viewer remembers two
more things across restarts:

- **Window position and size** — restored on the next launch. Saved on close in
  `~/.pdf-toolkit/window.json` (override: `PDF_TOOLKIT_WINDOW_FILE`). Fullscreen
  is **not** persisted; the underlying windowed rect is stored instead.
- **Last text-field placement** — the placement chooser (**Add text field**)
  floats your last pick to the top, remembered in `~/.pdf-toolkit/placement.json`
  (override: `PDF_TOOLKIT_PLACEMENT_FILE`). See `edit_mode/EDIT_MODE.md`.

Each store is independent and degrades to its default if missing or corrupt.

## Delete saved text fields

**Delete saved text fields for this document** removes the text-field layout for
the open PDF: it clears the fields from the page and deletes the JSON sidecar
(`document.json`) next to the PDF. It asks for confirmation first. The PDF itself
is not modified — only the saved field layout is discarded. See `edit_mode/EDIT_MODE.md`
for how the sidecar works.
