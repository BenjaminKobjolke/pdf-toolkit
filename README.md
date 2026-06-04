# pdf-toolkit

Small Python CLI toolkit for two PDF page operations, each with an automatic timestamped backup.

- `pdf-swap-pages.bat <pdf>` — swap the two pages of a 2-page PDF, overwriting the original.
- `pdf-delete-page.bat <page> <pdf>` — delete page `<page>` (1-based), overwriting the original.
- `pdf-delete-pages.bat <start> <end> <pdf>` — delete pages `<start>`..`<end>` (1-based, inclusive), overwriting the original.
- `pdf-merge-folder.bat <folder>` — merge every supported file (`.pdf`, `.jpg`, `.jpeg`, `.png`) in `<folder>` into `<folder>\merged.pdf`. Files are added in alphabetical order (case-insensitive). Subfolders are ignored. If `merged.pdf` already exists in the folder, it is backed up first.
- `pdft.bat` — interactive wizard that prompts for the operation (swap / delete single / delete range / merge folder / open GUI viewer) and its arguments. The PDF prompt has Tab-completion against `*.pdf` files in the current directory; the folder prompt has Tab-completion against subdirectories (powered by `prompt_toolkit`).
- `pdft_gui.bat [pdf]` — GUI viewer (PySide6) that renders the PDF page by page and lets you run swap / delete page / delete range / merge folder on it, with the same automatic backups. Optionally pass a PDF path to open on startup.

Every run first copies the original to `backup/YYYYMMDD-HHMM-<filename>.pdf`. The `backup/` directory is resolved relative to your current working directory, so when you run the tool from `C:\Users\me\Documents` the backup lands in `C:\Users\me\Documents\backup\`. Override with the `PDF_TOOLKIT_BACKUP_DIR` environment variable. The backup is created **before** validation, so if validation fails (e.g. swap on a 3-page PDF) the original is untouched but a backup still exists.

## Installation

Requires [`uv`](https://docs.astral.sh/uv/) on Windows.

```bat
install.bat
```

This creates `.venv\` via `uv sync` and runs the unit tests.

## Usage

From the project root (or any directory if installed globally — see below):

```bat
pdf-swap-pages.bat C:\path\to\two-page.pdf
pdf-delete-page.bat 2 C:\path\to\file.pdf
pdf-delete-pages.bat 1 10 C:\path\to\file.pdf
pdf-merge-folder.bat "E:\path\to\folder"
pdft.bat                                    REM interactive wizard
pdft_gui.bat C:\path\to\file.pdf            REM GUI viewer
```

Relative paths are resolved against your current working directory.

### GUI viewer

`pdft_gui.bat` (or the wizard's **Open GUI viewer** entry) opens a window that
renders the current PDF. Use **Prev/Next** to page through it; the toolbar
buttons run the operations on the open file:

- **Delete current page** — deletes the page you are viewing (after a confirm), then re-renders.
- **Delete range…** — prompts for a 1-based inclusive start/end.
- **Swap 2 pages** — swaps the two pages of a 2-page PDF.
- **Merge folder…** — pick a folder to merge into `<folder>\merged.pdf`.
- **Edit text** — toggle text-editing mode to place, style, move, and export text
  fields onto the page. See [docs/TEXT_EDITING.md](docs/TEXT_EDITING.md).

Every operation writes a backup first (same `backup/YYYYMMDD-HHMM-<name>.pdf`
format) and surfaces validation errors in a dialog.

### Make it a PDF handler (open PDFs by double-click)

```bat
pdft_gui_register.bat     REM register the viewer as a PDF handler (HKCU, no admin)
pdft_gui_unregister.bat   REM undo
```

`pdft_gui_register.bat` registers a per-user ProgID so the viewer appears in
Windows' *Open with* list for `.pdf`. Windows 11 does **not** let any tool set
the *default* app silently, so finish in the UI: right-click a PDF →
**Open with → Choose another app → PDF (pdf-toolkit viewer)** → tick **Always**.

Double-click opens are launched windowless via `pdft_gui.vbs` (no console flash),
and the working directory is set to the opened PDF's folder, so its backups land
in `<that folder>\backup\`.

### Build a standalone `.exe`

Some apps only let you associate a real `.exe` (not a `.bat`) to open files.
Build a self-contained GUI executable with PyInstaller:

```bat
tools\build_exe.bat
```

This produces `dist\pdft-gui.exe` — a single onefile, windowed (no console)
executable that bundles Python, PySide6, and pymupdf. It takes an optional PDF
path argument, so `dist\pdft-gui.exe C:\path\to\file.pdf` opens that PDF, and you
can point Windows' *Open with → Choose another app* at it.

Notes:

- Onefile startup is slightly slower than the `.bat` (it unpacks to a temp dir on
  each launch).
- `dist\` and `build\` are git-ignored; the build config `pdft-gui.spec` is
  committed. To change the icon or bundled modules, edit that spec.
- Requires the dev dependencies (`install.bat` / `uv sync --all-extras` installs
  PyInstaller).

## Install globally

If you keep a folder on `PATH` for command-line tools (e.g. `C:\cmdtools`), you can install the bats there in one step:

```bat
tools\install_global.bat
```

It prompts for the target directory (default `C:\cmdtools`), then writes `pdft.bat` (the interactive wizard) and `pdft_gui.bat` (the GUI viewer) into it. `pdft` asks which operation to run, lists `*.pdf` files in your current directory for selection, and dispatches to the right tool internally. The generated bats point back to this project's venv, so the toolkit stays installed in one place but is callable from anywhere.

Both commands:

1. Write `backup\YYYYMMDD-HHMM-<filename>.pdf`.
2. Mutate the original file (atomic temp-file replace).
3. Exit non-zero with a clear message on validation failure.

### Swap rules

- Refuses unless the input has **exactly 2 pages**.
- Refuses encrypted PDFs.

### Delete rules

- 1-based page number.
- Refuses out-of-range pages.
- Refuses if the input has only 1 page (would leave an empty PDF).

### Delete-range rules

- 1-based, inclusive on both ends (e.g. `1 10` deletes 10 pages).
- Refuses `end < start` (no auto-swap).
- Refuses if `end` exceeds the page count.
- Refuses if the range covers the whole PDF (would leave it empty).

### Merge-folder rules

- Supported file types: `.pdf`, `.jpg`, `.jpeg`, `.png` (case-insensitive).
- Flat scan only (no recursion into subfolders).
- Files are merged in alphabetical order by filename, case-insensitive.
- The output is always written as `<folder>\merged.pdf`.
- An existing `merged.pdf` in the folder is backed up to `backup/YYYYMMDD-HHMM-merged.pdf` before being overwritten and is excluded from the input list.
- RGBA PNGs (e.g. screenshots with alpha channels) are auto-converted to RGB JPEG before being placed into the PDF (via Pillow); other images pass through `img2pdf` losslessly.
- Refuses if the folder contains no supported files, or if any input PDF is encrypted.

## Development

```bat
tools\run_tests.bat              REM unit tests
tools\run_integration_tests.bat  REM integration tests
update.bat                       REM update deps + lint + tests
```

## Configuration

Environment variables (optional):

- `PDF_TOOLKIT_BACKUP_DIR` — override the backup directory (default `./backup`).
- `PDF_TOOLKIT_LOG_LEVEL` — `DEBUG`, `INFO`, `WARNING`, `ERROR` (default `INFO`).
