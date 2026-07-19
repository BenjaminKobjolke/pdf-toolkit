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
| **Open file…** | Prompt for a document (PDF / text / markdown / image / any plain-text file) and open it. |
| **Open folder…** | Browse to a folder (folders-only browser with a **[ use this folder ]** row) and open its alphabetically first openable file. |
| **Open file from recent / history…** | Pick from recently opened documents (see below). |
| **Open folder from recent / history…** | Pick from recently used folders; reopens the last file you opened from that folder (see below). |
| **Next file in directory** / **Previous file in directory** | Open the alphabetically next / previous openable file in the current document's folder (also **Alt+Right** / **Alt+Left**). Wraps at the ends; honors the Open-dialog filter and skips files the viewer can't render; prompts to save unsaved changes first. |
| **Save changes to original file** | Write the working copy back to the original (with a backup) — PDFs and images. See *Deferred saving*. |
| **Open containing folder in native file explorer** | Open the document's folder in the OS file explorer. |
| **Rename file…** | Rename the open PDF (and its sidecar) and reopen it. |
| **Copy file path to clipboard** | Copy the open PDF's full path. |
| **Copy file name to clipboard** | Copy the filename with extension. |
| **Copy file name without extension to clipboard** | Copy the filename stem (no `.pdf`). |
| **Copy page as image (W×H px)** / **at 50% (…)** / **at 25% (…)** | Render the current page to an image and put it on the clipboard — at original size (one pixel per PDF point; for image documents the native pixels), half, or quarter. Titles show the **actual output pixel size**, recomputed every time the palette opens. |
| **Copy current view (W×H px)** / **at 50% (…)** / **at 25% (…)** | Copy exactly what the viewer shows on screen (current zoom, scroll position, overlays) as an image — at full, half, or quarter size. Same live pixel-size titles. |
| **Close current document** | Offer to save unsaved changes, then return to the empty viewer. |
| **Reload** | Re-read the open document from disk, keeping the current page and zoom. |
| **Reload on changes (this time)** | Auto-reload the current document when it changes on disk — this document only (see *Reload on changes*). |
| **Reload on changes (make default)** | Toggle auto-reload for every opened document (persisted; reset via **Remembered settings…**). |
| **Toggle menu bar** | Show/hide the top menu bar (remembered across sessions). |
| **Toggle toolbar** | Show/hide the button toolbars (remembered across sessions). |
| **Toggle status bar** | Show/hide the footer status bar (remembered across sessions; see `STATUS_BAR.md`). |
| **Toggle fullscreen** | Enter/leave fullscreen for the current session (not remembered). |
| **GIF: play / pause** | Pause or resume the current animated GIF. Shown only when an animated GIF is open (see *Animated GIF*). |
| **Palette: width %…** | Set the palette width as a % of the window (see *Appearance settings*). |
| **Palette: height %…** | Set the palette height as a % of the window. |
| **Palette: font size…** | Set the palette font size in points (0 = default). |
| **Palette: opacity %…** | Set the palette window opacity. |
| **Palette: toggle borderless** | Show/hide the palette window frame. |
| **Dialogs: size %…** | Set how much of the window every list/picker dialog fills (see *Appearance settings*). |
| **Text/Markdown: toggle dark mode** | Light ⇄ dark reading theme for `.txt`/`.md` (only shown for those; see *Appearance settings*). |
| **Text/Markdown: font size…** | Base font size (pt) for `.txt`/`.md` rendering (only shown for those). |
| **Open dialog: toggle all files** | Open dialog lists every file ⇄ only the configured extensions (persisted). |
| **Open dialog: file extensions…** | Edit which extensions the Open dialog lists (e.g. `pdf, txt, md, ini`); switches back to extension-list mode. |
| **Single instance: toggle reuse existing window** | When on (default), launching the viewer with a file (e.g. double-click in Explorer) opens it in the already-running window instead of a new one (see *Single instance* below). |
| **Single instance: toggle focus window on open** | When on (default), a file forwarded to the running window also brings that window to the front with keyboard focus; when off, the file opens but the window stays in the background (see *Single instance* below). |
| **Outline: width…** | Stroke width (px) of the selected-element outline (see *Appearance settings*). |
| **Outline: type…** | Line type of the outline — Dashed or Solid. |
| **Outline: color…** | Color of the outline (keyboard-first picker). |
| **Link overlay: font size…** | Letter font size of the link-hint overlay (see *Appearance settings*). |
| **Link overlay: text color…** | Color of the hint letter. |
| **Link overlay: background color…** | Fill of the chip behind the hint letter. |
| **Link overlay: box color…** | Outline color of the box around each link. |
| **Exit** | Close the viewer. |
| **Help: Show keyboard and mouse controls** | Open the F1 chooser: edit keyboard shortcuts (Del deletes) or view mouse controls (also **F1**). |
| **Previous page** / **Next page** | Step one page back / forward. |
| **First page** / **Last page** | Jump to the first / last page. |
| **Zoom to fit** | Scale the page to fit the window. |
| **Zoom 100%** | Show the page at true PDF size. |
| **Zoom in 10%** / **Zoom out 10%** | Scale up / down by 10%. |
| **Swap 2 pages** | Swap the two pages of a 2-page PDF. |
| **Delete current page** | Delete the page on screen (asks first). |
| **Delete page range…** | Delete an inclusive range of pages. |
| **Rotate page 90° left** / **90° right** / **180°** | Rotate the current page — for image documents, the image itself (also `Ctrl+Shift+R` / `Ctrl+R`). |
| **Flip page horizontally** / **vertically** | Mirror the current page (PDFs) or the image itself (image documents). |
| **Move page to next position** / **previous position** | Swap the current page one step forward / back. |
| **Move page to first** / **to last** | Move the current page to the start / end. |
| **Merge folder…** | Merge a folder of PDFs and images into `merged.pdf`. |
| **Open link** | Enter vim-style link-hint mode: label every link on the page, type the letter to open it (see below). |
| **Copy link** | Same hint overlay as **Open link**, but the letter copies the URL to the clipboard instead of opening it. |
| **Toggle edit mode** | Turn edit mode on / off (see `edit_mode/EDIT_MODE.md`). |
| **Select next / previous editable element** | Cycle selection through text fields and images (also **Tab** / **Shift+Tab**). |
| **Add text field** | Add a new text field (edit mode only). |
| **Add image…** | Place an image — e.g. a signature — on the page (edit mode only). |
| **Image: scale…** / **Image: delete** | Resize or remove the selected image. |
| **Delete selected field** | Remove the selected text field(s) (edit mode only). |
| **Export to PDF (text + images)** | Flatten the placed overlay into the document (deferred until save). |
| **Delete saved text fields for this document** | Delete this PDF's saved fields and its JSON sidecar. |
| **Configure keyboard shortcuts…** | Bind, rebind, or clear a command's keyboard shortcut (see `CONFIGURE_SHORTCUTS.md`). |
| **File type associations…** | Checklist of all supported file types (PDF, text, markdown, images) — check the ones FastFileViewer should offer to open; unchecking all removes the registration (Windows only; see `FILE_ASSOCIATIONS.md`). |
| **Remembered settings…** | Reset stored preferences (placement, image choice, palette, outline, keyboard shortcuts, …) individually or all. |
| **Search document text…** | Live full-text search of the document (see below). |
| **Search text fields…** | Live search of your placed text fields (see below). |
| **Clear search highlights** | Remove the gold match highlights (shown only while highlights exist). |

When a text field is **selected**, these extra commands appear in the palette
(and only then):

| Command | What it does |
|---------|--------------|
| **Field: change text…** | Edit the selected field's text. |
| **Field: font size…** | Type a new point/pixel size. |
| **Field: font family…** | Searchable list of installed fonts. |
| **Field: text color…** | Keyboard-first color picker (see below). |
| **Field: background color…** | Same picker for the field's fill. |
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

Page edits (rotate, flip, move, delete, swap — for image documents rotate/flip
transform the image itself), **Export text to PDF**, and your text-field
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
| **Ctrl+F** | Search document text |
| **Ctrl+Shift+F** | Search text fields |
| **Ctrl+Shift+H** | Clear search highlights |
| **Page Down** / **Page Up** | Next / previous page |
| **Home** / **End** | First / last page |
| **Alt+Right** / **Alt+Left** | Next / previous file in directory |
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
| **Dialogs: size %…** | 20–100 | Width **and** height of every other list/picker dialog — file browser (Open/Save/folder), the recent file/folder pickers, font and color pickers, search, and the small option menus — as a percentage of the main window (default 60). The palette itself keeps its own width/height settings above. |

Settings persist in a global file:

```
~/.pdf-toolkit/palette.json
```

The location can be overridden with the `PDF_TOOLKIT_PALETTE_FILE` environment
variable. A missing or corrupt file falls back to the defaults (width 80%,
height 60%, default font, opaque, framed).

### Text / Markdown appearance

For `.txt` and `.md` documents (which render through an HTML engine), two palette
commands — shown only when such a file is open — tune the reading experience and are
remembered across sessions:

| Command | Range | Effect |
|---------|-------|--------|
| **Text/Markdown: toggle dark mode** | — | Light ⇄ dark theme (light-on-dark). |
| **Text/Markdown: font size…** | 6–40 pt | Base font size; changing it re-paginates the document. |

`.md` files also render **formatted** (`##` → heading, bold, lists, code, links) rather
than as raw source. Persisted with the other settings in the sqlite backend; reset from
**Remembered settings…** ("Text/Markdown appearance"). See `FILE_FORMATS.md`.

### Selected-element outline

The dashed rectangle drawn around the **selected** text field or image in edit
mode is also tunable from the palette and remembered across sessions:

| Command | Range | Effect |
|---------|-------|--------|
| **Outline: width…** | 1–12 px | Stroke width of the outline (zoom-independent). |
| **Outline: type…** | Dashed / Solid | Line style of the outline. |
| **Outline: color…** | any color | Outline color (same picker as the field colors). |

Settings persist in `~/.pdf-toolkit/outline.json` (override:
`PDF_TOOLKIT_OUTLINE_FILE`). A missing or corrupt file falls back to the default
**2 px dashed red (`#FF0000`)** — chosen to stand out more than Qt's faint
built-in selection marquee. Reset it from **Remembered settings…**.

## Search

Both searches are **live**: type at least **3 characters** and results refresh on
every keystroke. Navigate with the arrow keys, **Enter** to act, **Esc** to close.

- **Search document text…** (`Ctrl+F`) lists **one row per match** — `Page N: …text…`.
  Selecting a match jumps to its page and draws a **gold highlight** around it.
  Highlights stay until you run **Clear search highlights** (`Ctrl+Shift+H`).
- **Search text fields…** (`Ctrl+Shift+F`) searches the text you placed via the
  editor. Selecting a result jumps to that page and **selects** the field (edit
  mode turns on) — its field commands then appear in the palette.

## Open link

**Open link** enters a vim-style hint mode over the current page. Every link gets
a green box and a small gold letter label; **type the letter** to open that link
in your default browser. **Esc** cancels. When a page has more than 26 links,
two-letter labels (`aa`, `ab`, …) are used and keystrokes are buffered until they
match. If the page has no links a **No links on this page** hint is shown and the
mode is not entered.

Both link kinds are detected: real PDF hyperlink annotations and bare
`http(s)://` URLs printed in the page text (a URL that is both is labelled once).

**Copy link** is the same overlay with a different action: the letter **copies the
URL to the clipboard** instead of opening it.

The overlay's appearance is tunable and remembered across sessions via the palette
— **Link overlay: font size… / text color… / background color… / box color…**
(letter size, letter color, chip fill, and box outline). Reset them from
**Remembered settings…** ("Link overlay appearance"). See `OPEN_LINK.md`.

## Color picker

The color commands open a keyboard-first picker:

- Type a **hex** value (`#ff8800`) or a **color name** (`white`, `black`, `red`,
  …) in the box.
- A **preview swatch** updates live as you type or move through the list.
- Recently used colors appear at the top, followed by common names.
- **Enter** accepts the typed value or the highlighted row; **Esc** cancels.

No new dependency — the picker is the same searchable dialog used elsewhere.

## Single instance

**Single instance: toggle reuse existing window** (on by default) controls what a
second launch does — e.g. double-clicking a file associated with
`FastFileViewer.bat`:

- **On**: the new process forwards the file to the already-running viewer (over a
  local named pipe), that window opens it and comes to the front, and the second
  process exits. A launch without a file just brings the running window to the
  front. The unsaved-changes prompt still appears if the current document is
  modified.
- **Off**: every launch opens its own viewer window (the previous behavior).

**Single instance: toggle focus window on open** (on by default) controls what
the running window does after it receives the file: bring itself to the front
and take keyboard focus (on), or open the file silently in the background
(off). To make the focus grab work on Windows — which normally blocks
background processes from stealing focus — the launching process grants its
foreground right to the running viewer (`AllowSetForegroundWindow`) before
forwarding.

The *launching* process reads the settings, so toggling either one takes effect
on the next launch — no restart of the running viewer needed. Persisted in the
sqlite settings backend; reset from **Remembered settings…** ("Reuse existing
window").

Known limitations: two launches in the same instant can still produce two
windows (self-heals on the next launch), and one file per launch is forwarded.

## Reload on changes

**Reload** re-reads the open document from disk once, keeping the current page and
zoom. **Reload on changes (this time)** watches the file and reloads automatically
whenever it changes on disk — for the current document only; opening another
document resets to the default. **Reload on changes (make default)** flips the
persisted default (off out of the box) so every opened document is watched;
"this time" still overrides it per document.

Details:

- Rapid successive changes (editors often write a file several times per save)
  are collapsed into one reload, and saving from the viewer itself (`Ctrl+S`)
  does **not** trigger a reload.
- If the document has unsaved changes when the file changes on disk, the usual
  **Save / Discard / Cancel** prompt appears; **Cancel** skips that reload.
- The default is persisted in the sqlite settings backend; reset it from
  **Remembered settings…** ("Reload on file changes").

## Animated GIF

Opening an animated `.gif` **plays it automatically**. The frames are decoded by
Qt's native movie engine and drawn onto the page, so zoom, fit, and scroll behave
just like any other image.

- **GIF: play / pause** stops the animation and resumes it — one palette row with a
  stable label (so a type-to-filter search for either "play" or "pause" always finds
  it). The command appears only while an animated GIF is open (a single-frame `.gif`
  is treated as a normal static image).
- Editing operations (rotate, flip, save) still apply to the first frame only; stop
  playback and treat the GIF as a still before transforming it (see `FILE_FORMATS.md`).

## Open file / folder from recent / history

The viewer records every PDF you open (most recent first, up to 100 entries) in a
global file:

```
~/.pdf-toolkit/recent.json
```

**Open file from recent / history…** shows that list — filename plus full path — in
the same type-to-filter dialog as the palette. Filter, select with the arrow keys,
and press **Enter** to open. The location can be overridden with the
`PDF_TOOLKIT_RECENT_FILE` environment variable.

**Open folder from recent / history…** shows the **unique folders** from the same
history (most-recent first). Picking a folder reopens the **last file you opened
from that folder**.

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
