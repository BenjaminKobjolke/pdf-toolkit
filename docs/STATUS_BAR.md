# Status Bar

The viewer's footer (`app/gui/mode_status_bar.py`, `ModeStatusBar`) is a thin
bar at the bottom of the window. It is **shown by default** (unlike the top
toolbar and menu bar, which are hidden by default), so the current mode and page
are in view out of the box. It can be hidden with **Toggle status bar** (see
below).

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ Regular Mode              5/7              ● Modified     │
└─────────────────────────────────────────────────────────┘
   ^ mode (left)        ^ page (centre)      ^ dirty (right)
```

- **Left — mode label.** Reads `Regular Mode` or `Edit Mode`, driven by the
  same `edit_mode_toggled` signal that switches the editor and toolbar, so it
  always reflects the real mode.
- **Centre — page indicator.** Shows `current/total` (e.g. `5/7`). It updates on
  every page change via the `page_changed` signal from `PageView`, and is blank
  when no document is open.
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
