# Bug: forwarded-open viewer stays in background when "focus on open" is off

**Status:** UNRESOLVED — issue still persists after the attempts below.

## Symptom

Single-instance forwarding. Viewer already running, buried behind other windows.
A second launch forwards a file over the named pipe (`pdf-toolkit-viewer`) and the
running viewer opens it. With **Single instance: toggle focus window on open**
(`focus_on_forward`) turned **off**, the file loads but the viewer window does not
come to the front — it stays behind whatever the user was in. Looks like nothing
happened.

Goal: with the setting **off**, bring the window to the **front** but do **not**
steal keyboard focus. (With it **on**, front + focus — that path works.)

## Relevant code

- Receiving side: `app/gui/main.py` → `_open_in()` and `_raise_above_others()`.
- Setting: `focus_on_forward` in `app/config/instance_settings.py`, read via
  `app/gui/instance_controller.py`.
- Launching side grants foreground right: `app/gui/single_instance.py` →
  `_allow_foreground_transfer()` calls `AllowSetForegroundWindow(-1)` before
  forwarding (this runs unconditionally, so foreground rights ARE handed over).

## What we tried

### Attempt 1 — always `raise_()` (drop the early return)

`_open_in` used to early-return when `focus_on_forward` was off. Changed it to
always `setWindowState(~Minimized)` + `show()` + `raise_()`, and only call
`activateWindow()` when the flag is on.

Result: **no change on Windows.** `raise_()` only reorders within our own app's
window stack — it does not lift the window above *other applications'* windows.

### Attempt 2 — topmost-flash trick (SetWindowPos)

Added `_raise_above_others()`: `SetWindowPos(HWND_TOPMOST)` then
`SetWindowPos(HWND_NOTOPMOST)`, both with `SWP_NOSIZE | SWP_NOMOVE |
SWP_NOACTIVATE`. Intent: jump the window to the top of the Z-order above other
apps without activating (no keyboard-focus steal). Wired into the `else` branch
of `_open_in`.

Result: **issue still persists.** Window still does not reliably come to the
front.

## Notes / hypotheses for next time

- Windows foreground/Z-order rules are strict: a background process generally
  cannot reorder itself above the foreground app's window without being granted
  foreground rights *and* actually taking foreground. `SWP_NOACTIVATE` may be
  exactly what prevents the reorder from sticking here.
- The `AllowSetForegroundWindow(-1)` grant from the launcher expires / is
  single-use and tied to the *foreground* transition — if we never call
  `SetForegroundWindow`/`activateWindow`, the grant may go unused and the
  topmost-flash has no privilege to reorder across apps. Worth testing whether
  the flash works *with* the grant vs the timing of when the launcher exits.
- Possible next approaches:
  - `FlashWindowEx` (taskbar flash) as an honest "look here" instead of forcing
    Z-order — lower ambition, but not misleading.
  - Briefly `activateWindow()` then immediately restore focus to the previous
    foreground window (`GetForegroundWindow` before, `SetForegroundWindow` back
    after) — janky, may flicker.
  - Accept that Windows won't allow front-without-focus and make the "off"
    setting mean taskbar-flash only, documenting the platform limit.
- The current code (Attempt 1 + 2) is left in place. Tests:
  `tests/unit/test_open_in_focus.py`.
