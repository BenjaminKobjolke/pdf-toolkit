# pdf-toolkit

Small Python CLI toolkit for two PDF page operations, each with an automatic timestamped backup.

- `pdf-swap-pages.bat <pdf>` — swap the two pages of a 2-page PDF, overwriting the original.
- `pdf-delete-page.bat <page> <pdf>` — delete page `<page>` (1-based), overwriting the original.
- `pdf-delete-pages.bat <start> <end> <pdf>` — delete pages `<start>`..`<end>` (1-based, inclusive), overwriting the original.
- `pdf-rotate-page.bat <page> <degrees> <pdf>` — rotate page `<page>` (1-based) clockwise by `<degrees>` (`90` = right, `180` = flip, `270` = left), overwriting the original.
- `pdf-move-page.bat <from> <to> <pdf>` — move page `<from>` to 1-based position `<to>`, overwriting the original.
- `pdf-insert-page.bat <insert> <after> <pdf>` — insert `<insert>` (a PDF or `.jpg`/`.jpeg`/`.png` image) after 1-based page `<after>` of `<pdf>` (`0` = before the first page), overwriting the original.
- `pdf-extract-page.bat <page> <pdf> [-o <out>]` — extract 1-based `<page>` into its own new file (default `<name>-pNN.pdf` beside the source); the original is left untouched, so no backup is made.
- `pdf-merge-folder.bat <folder>` — merge a folder into a single file. A folder of `.pdf`/`.jpg`/`.jpeg`/`.png` files becomes `<folder>\merged.pdf`; a folder of text files (`.txt`/`.md`) is concatenated into `<folder>\merged.txt` (or `merged.md` when all inputs are `.md`). Files are added in alphabetical order (case-insensitive). Subfolders are ignored, a mixed text-and-PDF folder is refused, and an existing `merged.*` is backed up first.
- `pdft.bat` — interactive wizard that prompts for the operation (swap / delete single / delete range / rotate / move / insert pages / extract page / merge folder / open GUI viewer) and its arguments. The PDF prompt has Tab-completion against `*.pdf` files in the current directory; the insert-file prompt completes PDFs + images; the folder prompt has Tab-completion against subdirectories (powered by `prompt_toolkit`).
- `pdft_gui.bat [file]` — GUI viewer (PySide6) that renders **PDF, `.txt`, and `.md`** documents page by page, with a **command palette** (`Ctrl+Shift+P`) for every action: page operations (rotate, move, delete, swap), zoom, navigation, full-text + field search, recent-document history, rename, and in-place editing of text fields and images. Each feature declares which formats it supports — reading, search, and links work on all three, while page operations and editing stay PDF-only (see [docs/FILE_FORMATS.md](docs/FILE_FORMATS.md)). `.md` renders as its raw source. Edits go to a temporary working copy and reach the original only when you **Save** (`Ctrl+S`); closing with unsaved changes prompts first. Press **F1** for the keyboard and mouse controls. Optionally pass a file path to open on startup.

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
renders the current document — **PDF, `.txt`, or `.md`** (see
[docs/FILE_FORMATS.md](docs/FILE_FORMATS.md) for what each feature supports per
format). The viewer is **keyboard-first**: the menu bar and button toolbars are
**hidden by default** (toggle them from the palette), so the command palette is the
primary way to drive it. Commands the open document's format can't use are greyed
out.

#### Command palette (`Ctrl+Shift+P`)

A searchable list of every action — type to filter (relaxed: `field del` finds
**Field: delete**), arrow keys to move, **Enter** to run, **Esc** to close.
Commands needing an open document are hidden until one is open. **Recently-run
commands float to the top** (most-recent first; the top one in bold), remembered
across restarts. Full reference:
[docs/COMMAND_PALETTE.md](docs/COMMAND_PALETTE.md).

The palette and direct shortcuts cover:

- **Document** — Open, **Open from recent / history…** (last 100 PDFs),
  **Rename file…** (renames the PDF and its text-field sidecar together),
  **Copy all text from current page** (to the clipboard), Close, Exit.
- **Pages** — Previous/Next, **First/Last**, Swap 2 pages, Delete current page,
  Delete range…, **Insert pages (PDF or image)…** (after the current page),
  **Extract current page to file…**, Merge folder…
- **Zoom** — Fit, 100% (true PDF size), in/out 10%. The zoom *mode* sticks as you
  change pages (fit re-fits each page).
- **Search** — **Search PDF text** (`Ctrl+F`, live, jump to a match + gold
  highlight that stays until **Clear highlights**) and **Search text fields**
  (`Ctrl+Shift+F`, jump to and select a placed field).
- **View** — **Toggle menu bar** / **Toggle toolbar** / **Toggle status bar**
  (remembered across runs) and **Toggle fullscreen** (session only). Window
  position and size are also remembered across runs.
- **Edit mode (text + images)** — toggle edit mode to place text fields and
  images (e.g. a transparent `signature.png`). When a field is selected the
  palette exposes its options (change text, font size/family, text + background
  color, bold/italic, delete); a selected image can be moved, scaled (corner
  handles, palette, or **+**/**-**, aspect locked), and deleted. Images are
  copied into an `assets/` folder next to the PDF or referenced in place. **Tab**
  / **Shift+Tab** cycle the editable elements. The **selected element's outline**
  (width, dashed/solid, color) is configurable from the palette — **Outline:
  width / type / color…** — and remembered across sessions (default 2px dashed
  red). See
  [docs/edit_mode/EDIT_MODE.md](docs/edit_mode/EDIT_MODE.md) (overview, links to
  [TEXT_EDITING.md](docs/edit_mode/TEXT_EDITING.md) and
  [IMAGE_EDITING.md](docs/edit_mode/IMAGE_EDITING.md)) and
  [docs/WIDGETS.md](docs/WIDGETS.md) (custom color picker — type a hex or name,
  pick transparent, recents + live preview).
- **Select mode (vim-style text copy)** — `Ctrl+Shift+S` enters a read-only mode
  that navigates the PDF's own text by keyboard: `h`/`j`/`k`/`l` (or arrow keys;
  plus `w`/`b`,
  `0`/`$`, `gg`/`G`) move a word cursor, `v` starts a visual selection, `y` copies
  it to the clipboard, `Esc`/`q` exits. Mutually exclusive with edit mode. The
  cursor **starts on the current search match** (after `Ctrl+F`) or wherever you
  **click**; `Esc` outside select mode clears the search highlight. See
  [docs/SELECT_MODE.md](docs/SELECT_MODE.md).
- **Open / copy link (vim-style link hints)** — **Open link** / **Copy link** in
  the palette label every link on the current page with a letter; type the letter
  to open that URL in the browser or copy it to the clipboard, `Esc` cancels.
  Detects both real PDF hyperlinks and bare printed `http(s)://` URLs (so URLs in
  `.txt` / `.md` documents get hints too). The overlay
  (letter size, letter color, chip background, box color) is configurable from the
  palette and remembered. See [docs/OPEN_LINK.md](docs/OPEN_LINK.md).
- **File browser (vim-style)** — opening, saving, and folder-picking use a custom
  keyboard-first browser instead of the OS dialog: `j`/`k` move, `l`/`Enter` enter
  a folder or pick a file, `h`/`Alt+↑`/`..` go up (drive list at a drive root), `/`
  filters. See [docs/FILE_BROWSER.md](docs/FILE_BROWSER.md).

#### Keyboard and mouse controls

| Key | Action |
|-----|--------|
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+F` / `Ctrl+Shift+F` | Search PDF text / text fields |
| `Ctrl+Shift+H` | Clear search highlights |
| `Ctrl+Shift+S` | Toggle text select mode (vim-style copy) |
| `Page Down` / `Page Up` | Next / previous page |
| `Home` / `End` | First / last page |
| `Ctrl++` / `Ctrl+-` / `Ctrl+0` | Zoom in / out / 100% |
| `Ctrl+↑` / `Ctrl+↓` | Zoom in / out 10% |
| `↑` / `↓` at the page edge | Previous / next page |
| `Wheel` / `Shift+Wheel` | Scroll vertically (flip at edge) / horizontally |
| `Ctrl+Wheel` | Previous / next page |

Full key + mouse map: [docs/KEYBOARD_SHORTCUTS.md](docs/KEYBOARD_SHORTCUTS.md).

A footer **status bar** shows the current mode (left) and page `current/total`
(centre); shown by default and hideable via **Toggle status bar** (remembered).
See [docs/STATUS_BAR.md](docs/STATUS_BAR.md). The palette window itself is tunable
(size, font, opacity, borderless), as is the selected-element outline (width,
type, color) — see the *Appearance settings* section of
[docs/COMMAND_PALETTE.md](docs/COMMAND_PALETTE.md).

Every page operation writes a backup first (same `backup/YYYYMMDD-HHMM-<name>.pdf`
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

This produces `dist\FastPDFToolkit.exe` — a single onefile, windowed (no console)
executable that bundles Python, PySide6, and pymupdf. It takes an optional PDF
path argument, so `dist\FastPDFToolkit.exe C:\path\to\file.pdf` opens that PDF, and you
can point Windows' *Open with → Choose another app* at it.

Notes:

- Onefile startup is slightly slower than the `.bat` (it unpacks to a temp dir on
  each launch).
- `dist\` and `build\` are git-ignored; the build config `pdft-gui.spec` is
  committed. To change the icon or bundled modules, edit that spec.
- The window and exe icon come from one source PNG; see
  [docs/APP_ICON.md](docs/APP_ICON.md) for the PNG → `.ico` workflow.
- Requires the dev dependencies (`install.bat` / `uv sync --all-extras` installs
  PyInstaller).

### Release notes

View **what's new** in the app via **File → Release notes…** (or the command
palette / the `pdft` wizard's *Show release notes*). Notes are bundled into the
exe and shown newest-first with Older/Newer navigation. The release is identified
by `<version>_<build>` (`pyproject.toml` + `build_version.txt`). To cut a release —
bump the build (`tools\build_increment.bat`), write `release_notes/<label>/en.json`,
translate, then `tools\build_release.bat` — see
[docs/CREATE_NEW_RELEASE.md](docs/CREATE_NEW_RELEASE.md).

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

### Insert-page rules

- `<insert>` may be a PDF (all its pages are inserted) or a `.jpg`/`.jpeg`/`.png` image (one page).
- `<after>` is 1-based; `0` inserts before the first page, `N` (the page count) appends at the end.
- Refuses out-of-range positions, encrypted source PDFs, and unsupported insert file types.
- In the GUI the inserted content lands after the page you are viewing, deferred until **Save** like the other page operations.

### Extract-page rules

- 1-based page number; refuses out-of-range pages and encrypted PDFs.
- Writes a **new** single-page file and never modifies the source, so no backup is created.
- Default destination is `<name>-pNN.pdf` beside the source; override with `-o <out>` (CLI) or the save dialog (GUI).

### Merge-folder rules

- Two kinds of folder, chosen by content:
  - **PDF / image** (`.pdf`, `.jpg`, `.jpeg`, `.png`) → pages concatenated into `<folder>\merged.pdf`.
  - **Text** (`.txt`, `.md`) → files read as UTF-8 and concatenated (blank line between them) into `<folder>\merged.<ext>` — the shared extension when uniform (all `.md` → `merged.md`), otherwise `merged.txt`.
- A folder **mixing** text with PDF/image files is refused.
- Flat scan only (no recursion into subfolders); case-insensitive on extension and sort.
- Files are merged in alphabetical order by filename.
- An existing `merged.{pdf,txt,md}` is backed up to `backup/YYYYMMDD-HHMM-merged.*` before being overwritten and is excluded from the input list.
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
- `PDF_TOOLKIT_RECENT_FILE` — recent-documents store (default `~/.pdf-toolkit/recent.json`).
- `PDF_TOOLKIT_UI_STATE_FILE` — remembered menu/toolbar/status-bar visibility (default `~/.pdf-toolkit/ui_state.json`).
- `PDF_TOOLKIT_COMMAND_HISTORY_FILE` — command-palette usage history for recency ordering (default `~/.pdf-toolkit/command_history.json`).
- `PDF_TOOLKIT_PLACEMENT_FILE` — last text-field placement mode (default `~/.pdf-toolkit/placement.json`).
- `PDF_TOOLKIT_WINDOW_FILE` — remembered window position/size (default `~/.pdf-toolkit/window.json`).
- `PDF_TOOLKIT_PALETTE_FILE` — command-palette appearance (size/font/opacity/borderless) (default `~/.pdf-toolkit/palette.json`).
- `PDF_TOOLKIT_IMAGE_CHOICE_FILE` — last image copy/reference choice (default `~/.pdf-toolkit/image_choice.json`).
- `PDF_TOOLKIT_OUTLINE_FILE` — selected-element outline appearance (width/type/color) (default `~/.pdf-toolkit/outline.json`).
