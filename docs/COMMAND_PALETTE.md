# Command Palette

The GUI viewer has a searchable command palette that exposes every viewer action
in one place — page operations, zoom, navigation, text editing, and document
management. It is the fastest way to reach a command without hunting through the
toolbar or menus.

## Opening the palette

Press **Ctrl+Shift+P** anywhere in the viewer, or use **File → Command palette…**.

A filter box opens over a command list:

- **Type** to filter commands by name (case-insensitive substring match).
- **Up / Down** move the selection (wrapping at the ends).
- **Enter** runs the highlighted command.
- **Esc** closes the palette without running anything.

Commands that need an open document (zoom, navigation, page edits, text edits)
are hidden until a PDF is open.

## Commands

| Command | What it does |
|---------|--------------|
| **Open PDF…** | Prompt for a PDF and open it. |
| **Open from history…** | Pick from recently opened documents (see below). |
| **Close current document** | Save pending text edits, then return to the empty viewer. |
| **Exit** | Close the viewer. |
| **Previous page** / **Next page** | Step one page back / forward. |
| **First page** / **Last page** | Jump to the first / last page. |
| **Zoom to fit** | Scale the page to fit the window. |
| **Zoom 100%** | Show the page at true PDF size. |
| **Zoom in 10%** / **Zoom out 10%** | Scale up / down by 10%. |
| **Swap 2 pages** | Swap the two pages of a 2-page PDF. |
| **Delete current page** | Delete the page on screen (asks first). |
| **Delete page range…** | Delete an inclusive range of pages. |
| **Merge folder…** | Merge a folder of PDFs and images into `merged.pdf`. |
| **Toggle text edit mode** | Turn text editing on / off (see `TEXT_EDITING.md`). |
| **Add text field** | Add a new text field (edit mode only). |
| **Delete selected field** | Remove the selected text field(s) (edit mode only). |
| **Export text to PDF** | Write text fields onto a `_text-embedded` copy. |
| **Delete saved text fields for this document** | Delete this PDF's saved fields and its JSON sidecar. |

## Keyboard shortcuts

Common commands also have direct keys, so you do not have to open the palette:

| Key | Command |
|-----|---------|
| **Ctrl+Shift+P** | Open the command palette |
| **Page Down** / **Page Up** | Next / previous page |
| **Home** / **End** | First / last page |
| **Ctrl++** (or **Ctrl+=**) | Zoom in 10% |
| **Ctrl+-** | Zoom out 10% |
| **Ctrl+0** | Zoom 100% |
| **Ctrl+F** | Zoom to fit |

Zoom level persists as you change pages.

## Open from history

The viewer records every PDF you open (most recent first, up to 100 entries) in a
global file:

```
~/.pdf-toolkit/recent.json
```

**Open from history…** shows that list — filename plus full path — in the same
type-to-filter dialog as the palette. Filter, select with the arrow keys, and
press **Enter** to open. The location can be overridden with the
`PDF_TOOLKIT_RECENT_FILE` environment variable.

## Delete saved text fields

**Delete saved text fields for this document** removes the text-field layout for
the open PDF: it clears the fields from the page and deletes the JSON sidecar
(`document.json`) next to the PDF. It asks for confirmation first. The PDF itself
is not modified — only the saved field layout is discarded. See `TEXT_EDITING.md`
for how the sidecar works.
