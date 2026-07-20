# Status Bar

The viewer's footer (`app/gui/mode_status_bar.py`, `ModeStatusBar`) is a thin
bar at the bottom of the window. It is **shown by default** (unlike the top
toolbar and menu bar, which are hidden by default), so the current mode and page
are in view out of the box. It can be hidden with **Toggle status bar** (see
below).

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ Regular Mode          5/7          150%    ● Modified     │
└─────────────────────────────────────────────────────────┘
   ^ mode (left)    ^ page (centre)  ^ zoom   ^ dirty (right)
```

- **Left — mode label.** Reads `Regular Mode` or `Edit Mode`, driven by the
  same `edit_mode_toggled` signal that switches the editor and toolbar, so it
  always reflects the real mode. In **Select mode** it instead shows the live
  key hints (`set_hint`), switching to a `-- VISUAL --` variant once a selection
  is started (see `SELECT_MODE.md`).
- **Centre — flash message + page indicator.** Command **success feedback**
  ("copied file path", "opened with Photoshop", …) flashes here for ~3 seconds
  via `flash(text)` — non-blocking, left of the page indicator; only errors
  open a modal dialog. The page indicator shows `current/total` (e.g. `5/7`),
  updates on every page change via the `page_changed` signal from `PageView`,
  and is blank when no document is open.
- **Right of centre — zoom indicator.** Shows the live zoom as `150%`
  (`strings.ZOOM_FMT`), where `100%` is the page's true PDF size. It updates via
  the `zoom_changed` signal from `PageView` whenever the zoom changes (fit, 100%,
  zoom in/out, or a window resize while fitting), and is blank when no document is
  open.
- **Right — unsaved-changes marker.** Shows `● Modified` (`strings.MODIFIED_MARKER`)
  once an edit has been made to the working copy but not yet saved to the original
  file; it clears on save, open, and close. Set via `set_dirty(on)`.

## Toggling visibility

**Toggle status bar** (command palette) shows/hides the footer. The choice is
persisted with the other window-chrome flags (menu bar, toolbars) in
`~/.pdf-toolkit/ui_state.json` via `UiStateStore`, and restored on the next
launch. `ChromeController` (`app/gui/chrome.py`) owns the show/hide + save; the
footer defaults to visible (`UiState.statusbar_visible=True`).

## Notes

- The page indicator format is `{current}/{total}` (`strings.PAGE_OF_FMT`). The
  top toolbar shows the longer `Page {current} / {total}` form; the footer uses
  the compact one because it sits centred.
- The footer owns no state — it is presentation only, fed by signals from the
  window. Tests cover it in `tests/unit/test_mode_status_bar.py`.
