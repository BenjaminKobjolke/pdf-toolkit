# Configuring Keyboard Shortcuts

Every keyboard shortcut in the GUI viewer is editable at runtime — add new ones,
rebind the built-ins, or clear them. Changes take effect **immediately** (no
restart) and are remembered across sessions. The built-in defaults (listed in
`KEYBOARD_SHORTCUTS.md`) behave exactly like shortcuts you set yourself: each one
can be overwritten, moved to another command, or removed.

## Seeing the current shortcut

The command palette (**Ctrl+Shift+P**) shows each command's shortcut
**right-aligned** on its row, so you always see what's bound to what. Press **F1**
for the full searchable key + mouse list.

## Changing a shortcut

1. Open the palette and run **Configure keyboard shortcuts…** (or bind a key to it
   first — it is an ordinary command).
2. A searchable command list opens — the same type-to-filter dialog as the
   palette, with each command's current chord shown on the right. Filter to the
   command you want and press **Enter**.
3. A small capture window appears: **press your shortcut** (e.g. hold **Alt** and
   press **W**). It shows the detected chord.
4. Press **Enter** to confirm, or **Esc** to cancel (Esc once clears the detected
   chord so you can try again; Esc again closes the window).

The new chord appears next to the command in the palette and works right away.

> **Example.** Open **Configure keyboard shortcuts…**, search `exit`, press
> **Enter**, then press **Alt+W**. Confirm with **Enter**. The palette now shows
> `Alt+W` on **Exit**, and pressing **Alt+W** closes the viewer.

### Reassigning a chord that's already taken

If the chord you press is already bound to another command, a prompt asks whether
to **reassign** it. Confirm to move the chord to the new command (the previous
command loses it); cancel to keep things as they are.

## Clearing a shortcut

In the **Configure keyboard shortcuts…** list, highlight a command and press
**Del**. After a confirmation prompt, every chord bound to that command is
removed. (A command can still be run from the palette even with no shortcut.)

## The command palette chord is rebindable too

**Ctrl+Shift+P** (open the palette) is a normal command and can be rebound or
cleared like any other. As a safety net, the palette is **always** reachable from
**File → Command palette…**, so you can never lock yourself out of it.

## Where it's stored

Your changes are kept as a small list of overrides in a global file:

```
~/.pdf-toolkit/keybindings.json
```

Each entry maps a chord to a command id (or marks a default chord as removed). The
location can be overridden with the `PDF_TOOLKIT_KEY_BINDINGS_FILE` environment
variable. A missing or corrupt file just means the built-in defaults apply.

## Resetting to defaults

Run **Remembered settings…** from the palette and reset **Keyboard shortcuts** (or
**Clear ALL**). This deletes the overrides file, restoring every built-in default
on the next change or restart.
