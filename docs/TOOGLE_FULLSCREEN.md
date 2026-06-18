# Toggle Fullscreen

The viewer can switch the main window in and out of fullscreen for the current
session. Fullscreen hides the OS window frame so the page fills the screen; it
is **not remembered across runs** — the window always reopens windowed.

## Reaching it

- **Command:** `Toggle fullscreen` (`strings.CMD_TOGGLE_FULLSCREEN`), command id
  `toggle_fullscreen` (`app/gui/commands.py`). Always enabled (no document
  required).
- Run it from the command palette, or bind a key to it via **Configure
  shortcuts** (see `docs/CONFIGURE_SHORTCUTS.md`). There is no default key.

## Behaviour

`MainWindow.toggle_fullscreen` (`app/gui/main_window.py`) flips the state and
delegates the window work to `WindowGeometryController`
(`app/gui/window_geometry_controller.py`):

- **Enter** — `enter_fullscreen()` snapshots the current windowed rectangle with
  `QWidget.saveGeometry()`, then calls `showFullScreen()`.
- **Leave** — `exit_fullscreen()` calls `showNormal()` to clear the fullscreen
  flag, then `restoreGeometry(snapshot)` to put the window back at the exact
  size **and** position it had before entering. The snapshot also carries a
  maximized state, so a maximized window returns maximized.

### Why the explicit snapshot

Relying on Qt's implicit `showNormal()` restore is unreliable on Windows when
the window geometry was set programmatically before the window was first shown
(the viewer applies the saved geometry via `resize()`/`move()` in
`WindowGeometryController.restore()` before `window.show()`). Without the
snapshot, leaving fullscreen could fall back to a default size instead of the
previous windowed rectangle. Capturing and restoring the geometry ourselves
fixes that.

## Persistence

Fullscreen state is session-only and never written to disk. The window's
windowed position/size *is* persisted on close — `WindowGeometryController.save()`
stores the underlying windowed rect (`normalGeometry()`, ignoring fullscreen /
maximized framing) to `~/.pdf-toolkit/window.json`, so a session that ends in
fullscreen still reopens windowed at the right place. See `docs/STATUS_BAR.md`
for the related window-chrome flags (menu bar, toolbars, status bar), which —
unlike fullscreen — *are* remembered.

## Tests

- `tests/integration/test_gui_window.py::test_toggle_fullscreen_is_session_only`
  — enter/leave flips `isFullScreen()`.
- `tests/integration/test_gui_window.py::test_leaving_fullscreen_restores_pre_fullscreen_size`
  — leaving fullscreen restores the pre-fullscreen window size.
