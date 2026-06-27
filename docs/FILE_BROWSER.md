# File Browser (vim-style)

Opening, saving, and folder-picking use a **custom keyboard-first file browser**,
not the OS-native dialog. A cursor hops between directory entries vim-style:
`j`/`k` move, `l` enters a folder or picks a file, `h` goes up, `Enter` chooses.

The native `QFileDialog` ignored the app's keyboard-only workflow and its palette
chrome, so it was replaced everywhere a file or folder is chosen. The browser is a
`BaseDialog`, so it inherits the same font / opacity / frameless chrome as every
other dialog (see `CUSTOM_UI.md`).

## Where it appears

| Action | Entry point |
|--------|-------------|
| **Open PDF** (`Ctrl+O` / no-arg open) | `file_dialogs.prompt_open_file` |
| **Insert pages** (choose PDF/image) | `file_dialogs.prompt_open_file` |
| **Add image** | `file_dialogs.prompt_open_file` |
| **Save file as…** | `file_dialogs.prompt_save_file` |
| **Extract page to file** | `file_dialogs.prompt_save_file` |
| **Merge folder** (choose folder) | `file_dialogs.prompt_directory` |

Each returns a `Path`, or `None` when cancelled. They start in the current
document's folder (or the prefilled destination for save/extract).

## Keys

| Key | Action |
|-----|--------|
| **j** / **k** (or **↓** / **↑**) | Move down / up one entry |
| **gg** / **G** | First / last entry |
| **l** / **→** / **Enter** | Enter the highlighted folder, or pick the highlighted file |
| **h** / **←** / **Alt+↑** | Up one level (the `..` row does the same) |
| **/** | Type-ahead filter; **Enter** returns to the list, **Esc** clears it |
| **Tab** | (save only) jump to the filename field; **Enter** there saves the typed name |
| **Esc** / **q** | Cancel |

A **`..`** row tops every directory level. The current folder is shown above the
list; a two-row hint below it lists the keys.

## Going up past a drive

When you are already at a drive root (e.g. `E:\`) and go up (`h` / `Alt+↑` / `..`),
the list switches to the **mounted drives** (`C:\`, `D:\`, …). Pick one to enter it.
The drive list is read from the Windows `GetLogicalDrives` bitmask — it never stats
individual letters, so an absent floppy / disconnected network drive can't stall it.

## Modes

| Mode | Used by | Enter / pick behaviour |
|------|---------|------------------------|
| **Open** | open, insert, add image | `Enter`/`l` on a file picks it |
| **Save** | save-as, extract | `l` on a file copies its name into the field; `Enter` on a file overwrites it; `Tab` edits the name, `Enter` there saves |
| **Directory** | merge folder | only folders are listed; navigate in with `l`/`h`, `Enter` chooses the folder shown |

## How it fits together

- `app/gui/file_browser_model.py` — pure, Qt-free logic: `list_dir` (dirs first,
  then files matching the `FileFilter`, dotfiles skipped), `parent_of`,
  `substring_filter`, `is_root`, `drives`. Unit-tested in
  `tests/unit/test_file_browser_model.py`.
- `app/gui/file_browser_dialog.py` — `FileBrowserDialog(BaseDialog)`: the widget,
  the `..`/drive rows, and the vim key dispatch.
- `app/gui/file_dialogs.py` — the public `prompt_open_file` / `prompt_save_file` /
  `prompt_directory` helpers that build the dialog and return a `Path | None`.
- `app/gui/file_browser_strings.py` — titles, key hints, and the `FileFilter`
  presets (PDF, PDF-or-image, images, all).

Call the helpers **module-qualified** (`file_dialogs.prompt_open_file(...)`); tests
patch them at the module (`monkeypatch.setattr(file_dialogs, "prompt_open_file", …)`).
Wiring is covered by `tests/integration/test_file_browser_dialog.py` and
`tests/integration/test_insert_extract_gui.py`.
