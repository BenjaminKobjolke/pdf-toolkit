# Set as Default PDF Viewer

Two command-palette commands let you make FastFileViewer your Windows PDF handler
without leaving the viewer:

| Command | What it does |
|---------|--------------|
| **Set as default PDF viewer…** | Register the viewer as a PDF handler, then open the Windows **Default Apps** page with instructions. |
| **Remove as PDF handler** | Undo the registration (remove the viewer from the *Open with* list). |

Both are reached from the **Command palette** (`Ctrl+Shift+P`). See
`COMMAND_PALETTE.md`. They are **Windows-only** — on other platforms they are
hidden from the palette.

## What "register" actually does

Registering does **not** silently make the app your default. It only makes the
viewer a *choosable* handler by writing two things under your user account
(`HKCU`, no admin needed):

1. A ProgID `pdf-toolkit.Viewer` (display name *"PDF (pdf-toolkit viewer)"*).
2. An entry in the `.pdf` **Open with** list pointing at that ProgID.

Windows 8/10/11 protect the *active* default association (the `.pdf\UserChoice`
registry key) with a per-user signed hash that Microsoft keeps undocumented, so
**no third-party app — this one, the `.bat`, or any other tool — can set the
default for you.** That last step is yours:

1. In the **Default Apps** window that opens, find **".pdf"** (or the PDF file type).
2. Choose **"PDF (pdf-toolkit viewer)"**.
3. Set it as the default.

(Alternatively: right-click any `.pdf` → **Open with** → **Choose another app** →
pick *PDF (pdf-toolkit viewer)* → tick *Always use this app*.)

## Source (Python) vs. compiled exe — does it work either way?

Yes — but the command line written into the registry differs by how you run the
app, and each has a constraint.

| You run… | Registry `shell\open\command` | Keeps working as long as… |
|----------|-------------------------------|---------------------------|
| **Source / Python** (`.venv`) | `wscript.exe "…\FastFileViewer.vbs" "%1"` | the repo stays at the same path **and** the `.venv` (with deps) exists. The vbs sets the working dir to the PDF's folder and launches the GUI through the venv. |
| **Compiled exe** (PyInstaller) | `"…\FastFileViewer.exe" "%1"` | the exe stays at the same path. Self-contained — no venv, no scripts. |

So the **Python version works fine** for everyday use as long as you don't move
the repo or delete the virtual environment. The **compiled exe is the more
robust choice** for a permanent default, because it has no venv/script
dependencies — its only requirement is that the `.exe` not be moved. If you move
the repo, the venv, or the exe after registering, just run **Set as default PDF
viewer…** again to rewrite the path.

## Equivalent batch scripts

The same registration is available outside the GUI via the repo-root scripts the
commands are ported from:

- `FastFileViewer_register.bat` — register (source build).
- `FastFileViewer_unregister.bat` — remove the registration.
