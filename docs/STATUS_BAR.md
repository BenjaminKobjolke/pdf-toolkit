# Status Bar

The viewer's footer (`app/gui/mode_status_bar.py`, `ModeStatusBar`) is a thin
bar at the bottom of the window. It is **shown by default** (unlike the top
toolbar and menu bar, which are hidden by default), so the current mode and page
are in view out of the box. It can be hidden with **Toggle status bar** (see
below).

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ Regular Mode       File 2/25       150%    ● Modified     │
│                    Page 5/68                              │
└─────────────────────────────────────────────────────────┘
   ^ mode (left)  ^ file + page (centre)  ^ zoom  ^ dirty (right)
```

- **Left — mode label.** Reads `Regular Mode` or `Edit Mode`, driven by the
  same `edit_mode_toggled` signal that switches the editor and toolbar, so it
  always reflects the real mode. In **Select mode** it instead shows the live
  key hints (`set_hint`), switching to a `-- VISUAL --` variant once a selection
  is started (see `SELECT_MODE.md`).
- **Centre — flash message + file/page indicator.** Command **success feedback**
  ("copied file path", "opened with Photoshop", …) flashes here for ~3 seconds
  via `flash(text)` — non-blocking, left of the indicators; only errors
  open a modal dialog. Two stacked rows: the file indicator shows the open
  document's position among the openable files in its directory (`File 2/25`,
  computed on open via `file_browser_model.file_position`), and the page
  indicator shows `Page 5/68`, updating on every page change via the
  `page_changed` signal from `PageView`. Both rows are hidden when no document
  is open (empty rows collapse so the bar stays one row tall). Unpaged formats
  (images, GIFs — anything but PDF) show a bare `2/25` counter instead and no
  Page row (`set_paged_document(False)`, set per open from the file format).
- **Right of centre — zoom indicator.** Shows the live zoom as `150%`
  (`strings.ZOOM_FMT`), where `100%` is the page's true PDF size. It updates via
  the `zoom_changed` signal from `PageView` whenever the zoom changes (fit, 100%,
  zoom in/out, or a window resize while fitting), and is blank when no document is
  open.
- **Right — unsaved-changes marker.** Shows `● Modified` (`strings.MODIFIED_MARKER`)
  once an edit has been made to the working copy but not yet saved to the original
  file; it clears on save, open, and close. Set via `set_dirty(on)`. PSD documents
  never show it — their transforms are preview-only and can't be saved back
  (see `file_formats/PSD.md`).

## Toggling visibility

**Toggle status bar** (command palette) shows/hides the footer. The choice is
persisted with the other window-chrome flags (menu bar, toolbars) in
`~/.pdf-toolkit/ui_state.json` via `UiStateStore`, and restored on the next
launch. `ChromeController` (`app/gui/chrome.py`) owns the show/hide + save; the
footer defaults to visible (`UiState.statusbar_visible=True`).

## Font size

**Status bar: font size…** (command palette) prompts for a point size for the
whole footer (0 = default) — both this bar and the thumbnail **filter bar**
above it (the "Filter: …" row, see below). Persisted in the sqlite settings
backend via `StatusBarSettingsStore` (`app/config/status_bar_settings.py`),
applied by `StatusBarSettingsController` on launch and on change; reset from
**Remembered settings…** ("Status bar appearance"). Tests:
`tests/unit/test_status_bar_settings_controller.py`.

## Notes

- The page indicator format is `Page {current}/{total}` (`strings.LABEL_PAGE_FMT`,
  shared with the top toolbar); the file indicator is `File {current}/{total}`
  (`strings.FILE_OF_FMT`) for PDFs and the bare `{current}/{total}`
  (`strings.FILE_COMPACT_FMT`) for unpaged formats.
- The footer owns no state — it is presentation only, fed by signals from the
  window. Tests cover it in `tests/unit/test_mode_status_bar.py`.
- The thumbnail **filter bar** (the "Filter: …" label) is a separate footer row
  above this bar (created in `app/gui/thumbnails_controller.py`, not part of
  `ModeStatusBar`) and is unaffected by **Toggle status bar** — but it shares
  the font-size setting above. See `THUMBNAIL_VIEW.md`.
