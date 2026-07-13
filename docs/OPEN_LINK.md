# Open / Copy Link (vim-style link hints)

Open-link mode lets you **open any link on the current page with the keyboard**,
vim-style — every link gets a letter label, and typing the letter opens that URL
in your default browser. **Copy link** is the same overlay but the letter **copies
the URL to the clipboard** instead. Neither changes the document.

The page is rendered as a bitmap, so there is nothing to click through. Open-link
mode reads the links from the PDF instead (via PyMuPDF in `app/pdf/links.py`) and
draws a hint over each one.

## Turning it on

| How | |
|-----|--|
| Command palette | **Open link** (open in browser) or **Copy link** (copy URL) |

A document must be open. There is no default keyboard chord — bind one via
**Configure keyboard shortcuts…** if you want (see `CONFIGURE_SHORTCUTS.md`).

If the current page has **no links**, the footer shows **No links on this page**
and the mode is not entered.

## What gets a hint

Both kinds of link are detected:

- **PDF hyperlink annotations** — real clickable links (e.g. a blue underlined
  URL), read from `page.get_links()`.
- **Bare printed URLs** — `http(s)://` text found on the page, even when it is not
  a clickable annotation. Trailing punctuation is trimmed.

A URL that is both (printed *and* hyperlinked to the same target) is labelled
once.

## Keys

Each link shows a **green box** with a small **gold letter chip**. Type the
letter to open it.

| Key | Action |
|-----|--------|
| **a**, **b**, **c**, … | Open the link with that label |
| **Esc** | Leave open-link mode |

**More than 26 links:** two-letter labels are used (`aa`, `ab`, …) and your
keystrokes are buffered until they match a label. A keystroke that can't start
any label resets the buffer.

Single-page scope: only the links on the page you are viewing are labelled.

## Appearance

The overlay is tunable from the palette and **remembered across sessions**:

| Command | Effect |
|---------|--------|
| **Link overlay: font size…** | Point size of the hint letter (6–40). |
| **Link overlay: text color…** | Color of the hint letter (default black). |
| **Link overlay: background color…** | Fill of the chip behind the letter (default gold). |
| **Link overlay: box color…** | Outline color of the box around each link (default green). |

Colors use the keyboard-first picker (`WIDGETS.md`). Reset every value from
**Remembered settings…** ("Link overlay appearance").

## How it fits together

- `app/pdf/links.py` — `page_links()` returns typed `LinkBox` values (rect in PDF
  points + `uri`), annotations first, then printed URLs not already covered.
  Unit-tested in `tests/unit/test_links.py`.
- `app/gui/link_hints.py` — the on-page overlay: a box and a letter chip per
  link, scaled by the same `render.DEFAULT_ZOOM` the search/select overlays use,
  with colors/font read from the shared `LinkHintStyle` holder.
- `app/gui/link_hint_controller.py` — owns the mode state, assigns the labels
  (`hint_labels()`), dispatches the keys, and runs the terminal action:
  `open()` (stdlib `webbrowser.open()`) or `copy()` (clipboard). Key capture
  reuses the page-view interceptor and is restored to select mode on exit.
- `app/config/link_hint_settings.py` + `app/gui/link_hint_style.py` +
  `app/gui/link_hint_settings_controller.py` — the remembered appearance: a
  `RecordStore` (font size + three colors), the shared holder the overlay reads,
  and the controller behind the **Link overlay: …** palette commands. Mirrors the
  selection-outline settings trio.

Wiring is covered end-to-end by `tests/integration/test_link_hint_mode.py`;
the store is unit-tested in `tests/unit/test_link_hint_settings.py`.
