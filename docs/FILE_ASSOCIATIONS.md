# File Type Associations

One command-palette command manages which file types FastFileViewer is
associated with on Windows — without leaving the viewer:

| Command | What it does |
|---------|--------------|
| **File type associations…** | Open a checklist of all supported file types (`.pdf`, `.txt`, `.md`, and the image formats). Check the ones FastFileViewer should offer to open; OK applies the registration and opens the Windows **Default Apps** page for the final step. Unchecking everything removes the registration completely. |

It is reached from the **Command palette** (`Ctrl+Shift+P`), see
`COMMAND_PALETTE.md`, and is **Windows-only** — on other platforms it is hidden
from the palette. The checkboxes reflect the *live registry state*, so the
dialog always shows what is currently associated, even if you changed it
outside the app.

The dialog is keyboard-first: **Up/Down** move through the types, **Space**
toggles the highlighted one, and **Tab** reaches the **Select all** /
**Unselect all** buttons and OK/Cancel.

## What checking a type actually does

Checking does **not** silently make the app your default. It only makes the
viewer a *choosable* handler by writing per-user keys (`HKCU`, no admin):

1. A ProgID `pdf-toolkit.Viewer` (display name *"FastFileViewer"*).
2. An entry in each checked extension's **Open with** list pointing at that ProgID.
3. An app registration (`RegisteredApplications` + `Capabilities`) so
   FastFileViewer shows up as one app — with all its checked types — in the
   Windows **Default Apps** page.

Windows 8/10/11 protect the *active* default association (each extension's
`UserChoice` registry key) with a per-user signed hash that Microsoft keeps
undocumented, so **no third-party app — this one, the `.bat`, or any other
tool — can set the default for you.** That last step is yours:

1. In the **Default Apps** window that opens (on Windows 11 it deep-links
   straight to the FastFileViewer page), pick the file types you want.
2. Set **FastFileViewer** as their default.

(Alternatively: right-click any file → **Open with** → **Choose another app** →
pick *FastFileViewer* → tick *Always use this app*.)

## Source (Python) vs. compiled exe — does it work either way?

Yes — but the command line written into the registry differs by how you run the
app, and each has a constraint.

| You run… | Registry `shell\open\command` | Keeps working as long as… |
|----------|-------------------------------|---------------------------|
| **Source / Python** (`.venv`) | `wscript.exe "…\FastFileViewer.vbs" "%1"` | the repo stays at the same path **and** the `.venv` (with deps) exists. The vbs sets the working dir to the file's folder and launches the GUI through the venv. |
| **Compiled exe** (PyInstaller) | `"…\FastFileViewer.exe" "%1"` | the exe stays at the same path. Self-contained — no venv, no scripts. |

So the **Python version works fine** for everyday use as long as you don't move
the repo or delete the virtual environment. The **compiled exe is the more
robust choice** for a permanent default, because it has no venv/script
dependencies — its only requirement is that the `.exe` not be moved. If you move
the repo, the venv, or the exe after registering, just run **File type
associations…** again and press OK — applying rewrites the launch path.

## How it fits together

- `app/os_integration/file_association.py` — all registry logic. Declarative
  `set_associations(checked)` (registers checked extensions, unregisters the
  rest, tears everything down when empty), `registered_extensions()` read-back,
  and the `python -m …` CLI the bats wrap. The extension list derives from the
  `FileFormat` enum (`app/pdf/file_format.py`) — one source of truth. Unit-tested
  against an in-memory fake winreg in `tests/unit/test_file_association.py`.
- `app/gui/file_association_dialog.py` — the checklist dialog (keyboard-first:
  arrows + Space, Select all / Unselect all). Unit-tested in
  `tests/unit/test_file_association_dialog.py`.
- `app/gui/default_app_actions.py` — the palette action: read state → dialog →
  apply → open Default Apps (deep-linked on Win11). Strings in
  `app/gui/default_app_strings.py`. Integration-tested in
  `tests/integration/test_file_association_command.py`.

## Equivalent batch scripts

The same registration is available outside the GUI via the repo-root scripts,
which are thin wrappers over the same Python module
(`python -m app.os_integration.file_association`):

- `FastFileViewer_register.bat` — associate **all** supported file types.
- `FastFileViewer_unregister.bat` — remove the registration completely.

For a per-type selection, use the in-app dialog.
