# Custom Widgets

The GUI viewer ships a small family of **keyboard-first dialogs** that share the
same look and interaction: a filter box on top, a list below, and
Up/Down/Enter/Esc navigation. They live in `app/gui/` and are reused across the
command palette, search, history, font selection, and colour selection.

| Widget | File | Used for |
|--------|------|----------|
| `FilterListDialog` | `filter_list_dialog.py` | Command palette, history, font picker, live search |
| `ColorPickerDialog` | `color_picker_dialog.py` | Text + background colour |
| `TextInputDialog` | `text_input_dialog.py` | Multi-line field text (Ctrl+Enter to apply) |

Shared keys: **Up/Down** move (wrapping), **Enter** accept, **Esc** cancel.

## Colour picker (`ColorPickerDialog`)

A keyboard-first replacement for Qt's mouse-oriented `QColorDialog`. Used by the
**Field: text colour…** and **Field: background colour…** commands.

### Layout

```
┌─────────────────────────────────────┐
│ Type a hex (#ff8800) or name (white) │  ← filter / value entry
├─────────────────────────────────────┤
│ ███████████████████████████████████ │  ← live preview swatch
├─────────────────────────────────────┤
│ transparent                         │  ← (background only)
│ #123456            #123456          │  ← recently used, most recent first
│ black              #000000          │
│ white              #ffffff          │  ← curated common names
│ red                #ff0000          │
│ …                                   │
└─────────────────────────────────────┘
```

### Behaviour

- **Type a value.** Enter a hex (`#ff8800`) or any Qt colour name (`white`,
  `black`, `red`, …) in the box. Anything `QColor` accepts is valid.
- **Live preview.** The swatch recolours as you type or move through the list.
- **Recents first.** The most recently used colours appear at the top, followed
  by a curated set of common names (`COMMON_COLORS`).
- **Filter.** Typing also narrows the list (substring match on name or hex), so
  `00` or `gray` jumps straight to matches.
- **Accept / cancel.** **Enter** accepts the highlighted row, or the typed value
  if no row matches; **Esc** cancels (no change).

### Return value

`chosen()` returns:

- a normalised `#rrggbb` string, or
- `ColorPickerDialog.TRANSPARENT` when the transparent option is picked, or
- `None` when the dialog was cancelled.

Callers must distinguish `TRANSPARENT` from `None` — the first means "set no
fill", the second means "leave unchanged".

### Transparent (background only)

Constructed with `allow_transparent=True`, the picker lists a **transparent**
entry first (and accepts the typed words `transparent` / `none`). Choosing it
returns the `TRANSPARENT` sentinel; the field's background is then cleared
(`bg_color = None`), i.e. no fill is drawn behind the text. Text colour uses
`allow_transparent=False`, so it always yields a concrete colour.

Recently-used tracking ignores the transparent sentinel — only real colours are
remembered.

## Filter list dialog (`FilterListDialog`)

The general type-to-filter list. Two modes:

- **Static** — given a fixed list of `ListEntry` rows, filtered locally.
  Matching is **token-AND**: every whitespace-separated word must appear, in any
  order, so `field del` finds **Field: delete**.
- **Live (`provider`)** — given a callback, rows are recomputed on every
  keystroke once `min_chars` are typed. Used by PDF and field search.

Each `ListEntry` carries a `title`, optional `subtitle`, an `enabled` flag, and
an opaque `payload` the caller interprets (a command, a path, a search hit, …).

## Multi-line text input (`TextInputDialog`)

Used by **Field: change text…**. A plain-text editor where **Enter** inserts a
newline and **Ctrl+Enter** (or Ctrl+Return) applies; **Esc** cancels.
