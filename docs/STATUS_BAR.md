# Status Bar

The viewer's footer (`app/gui/mode_status_bar.py`, `ModeStatusBar`) is a thin
always-visible bar at the bottom of the window. Unlike the top toolbar and menu
bar — both hidden by default — the footer stays visible regardless of the chrome
toggles, so the current mode and page are always in view.

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ Regular Mode              5/7              ● Modified     │
└─────────────────────────────────────────────────────────┘
   ^ mode (left)        ^ page (centre)      ^ dirty (right)
```

- **Left — mode label.** Reads `Regular Mode` or `Edit Text Mode`, driven by the
  same `edit_mode_toggled` signal that switches the editor and toolbar, so it
  always reflects the real mode.
- **Centre — page indicator.** Shows `current/total` (e.g. `5/7`). It updates on
  every page change via the `page_changed` signal from `PageView`, and is blank
  when no document is open.
- **Right — unsaved-changes marker.** Shows `● Modified` (`strings.MODIFIED_MARKER`)
  once an edit has been made to the working copy but not yet saved to the original
  file; it clears on save, open, and close. Set via `set_dirty(on)`.

## Notes

- The page indicator format is `{current}/{total}` (`strings.PAGE_OF_FMT`). The
  top toolbar shows the longer `Page {current} / {total}` form; the footer uses
  the compact one because it sits centred and is always visible.
- The footer owns no state — it is presentation only, fed by signals from the
  window. Tests cover it in `tests/unit/test_mode_status_bar.py`.
