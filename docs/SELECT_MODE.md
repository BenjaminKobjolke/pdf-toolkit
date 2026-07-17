# Text Select Mode (vim-style)

Select mode lets you **navigate and copy the PDF's own text with the keyboard**,
vim-style — a cursor hops from word to word, `v` starts a visual selection, and
`y` copies it to the clipboard. It is read-only: it never changes the document.

The page is rendered as a bitmap, so there is no on-screen text layer to drag a
mouse over. Select mode drives selection from the PDF's word geometry instead
(extracted via PyMuPDF in `app/pdf/words.py`), which is why navigation is by
**word**, not by character.

## Turning it on

| How | |
|-----|--|
| **Ctrl+Shift+S** | Toggle text select mode |
| Command palette | **Toggle text select mode (vim)** |

A document must be open. The footer status bar shows the current keys while the
mode is active (see `STATUS_BAR.md`). Select mode and **Edit mode** are mutually
exclusive — entering one leaves the other.

Single-page scope: a selection stays within the current page. Changing pages
reloads the words and resets the cursor to the first word.

## Where the cursor starts

- **From a search match.** If you **Search document text** (`Ctrl+F`) first, the match
  is highlighted gold; entering select mode then **starts the cursor on that
  word** (the match's first word) and consumes the gold highlight. With no active
  highlight the cursor starts on the page's first word.
- **By click.** While in select mode, **left-click any word** to move the cursor
  there.

`Esc` outside select mode clears an active search highlight (same as **Clear
highlights**, `Ctrl+Shift+H`).

## Keys

Movement (the cursor outlines the current word):

| Key | Motion |
|-----|--------|
| **h** / **l** (or **←** / **→**) | Previous / next word (reading order) |
| **b** / **w** | Previous / next word (same as `h`/`l` at word granularity) |
| **j** / **k** (or **↓** / **↑**) | Down / up one line, nearest word by horizontal position |
| **0** / **$** | First / last word of the current line |
| **gg** / **G** | First / last word of the page |

Selecting and copying:

| Key | Action |
|-----|--------|
| **v** | Start (or cancel) a visual selection, anchored at the cursor |
| **y** | Copy the selected span to the clipboard, then drop the selection |
| **Esc** / **q** | Leave select mode |

With no visual selection active, **y** copies the single word under the cursor.

Copied text joins words with **spaces within a line** and a **newline between
lines**, so multi-line selections paste with their line breaks preserved.

## Copying a whole page

To grab the entire current page without navigating word by word, run **Copy all
text from current page** from the command palette — it copies the page's full
text (native line breaks preserved) to the clipboard. Works with or without
select mode.

## How it fits together

- `app/pdf/words.py` — `page_words()` returns typed `WordBox` values in PDF
  points, in reading order (fitz `get_text("words", sort=True)`).
- `app/gui/select_motions.py` — the pure cursor math (no Qt): one function per
  motion plus `span_text()` for the yank. Unit-tested in
  `tests/unit/test_select_motions.py`.
- `app/gui/selection_highlights.py` — the on-page overlay: a blue outline for the
  cursor word and a translucent fill for the selection, scaled by the same
  `render.DEFAULT_ZOOM` the search highlights use.
- `app/gui/select_controller.py` — owns the mode state, dispatches the keys, and
  writes the yank to `QApplication.clipboard()`.

The default chord lives in `app/gui/window_input.py` (`_SHORTCUTS`) and is
rebindable like every other shortcut — see `CONFIGURE_SHORTCUTS.md`. Wiring is
covered end-to-end by `tests/integration/test_select_mode.py`.
