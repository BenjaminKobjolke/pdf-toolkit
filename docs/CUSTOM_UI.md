# Custom Dialog UI

Every small window in the GUI viewer — confirmations, value prompts, alerts, the
command palette, search, color and font pickers — is a **custom keyboard-first
dialog**, not a bare Qt default. They share one base, so they look the same and all
honour the user's command-palette appearance (font size, opacity, frameless chrome).

This replaced the stock `QMessageBox` (delete-page confirm, unsaved-changes, errors)
and `QInputDialog` (palette font size, image scale, rename, zoom) windows, which
ignored the palette font and looked out of place. The native `QFileDialog` is also
gone — file open / save / folder picking now uses a custom keyboard-first browser
(`FileBrowserDialog`); see `FILE_BROWSER.md`.

`docs/WIDGETS.md` documents the keyboard-first **list** dialogs in detail (filter box +
list). This file documents the **system underneath them** and the confirm / input / alert
family.

## Architecture

Three layers in `app/gui/`, smallest first:

| Layer | File | Responsibility |
|-------|------|----------------|
| Shared chrome | `dialog_appearance.py` | Holds the live appearance and applies it. |
| Base dialog | `base_dialog.py` | `BaseDialog(QDialog)` — adopts the chrome when shown. |
| Form skeleton | `form_dialog.py` | `FormDialog(BaseDialog)` — message → content → buttons. |

### `dialog_appearance.py`

A module-level holder of the current `PaletteSettings`, mirroring the
`outline_style.active()` / `set_active()` pattern:

- `active()` / `set_active(settings)` — get/replace the live appearance.
- `apply_chrome(dialog, settings)` — apply **font size, opacity, frameless flag** to a
  dialog. This is the *single source* for those three properties; the palette's own
  applier (`palette_appearance.apply_appearance`) delegates to it after doing its
  window-relative resize.

`PaletteController` re-registers the settings via `set_active()` on load and after every
edit, so changing the palette font / opacity / borderless takes effect on the **next**
dialog opened — no restart, no per-dialog wiring.

### `base_dialog.py`

```python
class BaseDialog(QDialog):
    def apply_active_chrome(self) -> None:
        dialog_appearance.apply_chrome(self, dialog_appearance.active())

    def exec(self) -> int:
        self.apply_active_chrome()
        return super().exec()
```

Any dialog that extends `BaseDialog` adopts the appearance automatically. The existing
list dialogs (`FilterableListDialog`, and through it `FilterListDialog` /
`ColorPickerDialog`), `KeyCaptureDialog`, and `TextInputDialog` all extend it.

### `form_dialog.py`

`FormDialog(BaseDialog)` is the shared skeleton for the confirm / alert / number / text
dialogs — they all stack the same way:

```
┌──────────────────────────────┐
│ message (optional, wrapped)  │
├──────────────────────────────┤
│ [ content widget, optional ] │  ← spin box / line edit / nothing
├──────────────────────────────┤
│            [ OK ] [ Cancel ]  │  ← QDialogButtonBox
└──────────────────────────────┘
```

- `add_content(widget)` — insert the value-editing widget.
- `add_ok_cancel()` — standard OK/Cancel row wired to accept/reject.
- `add_buttons(box)` — for a custom `QDialogButtonBox`.
- `exec_value(dialog, reader)` — run modally; return `reader()` on accept, else `None`.

## Appearance inheritance

Dialogs inherit three things from the command-palette settings:

| Property | Source field | Effect |
|----------|--------------|--------|
| Font size | `font_pt` (0 = default) | `setFont` cascades to the filter box, list, labels, inputs. |
| Opacity | `opacity_pct` | Window transparency. |
| Frameless | `borderless` | OS window frame on/off. |

They do **not** inherit the palette's window-relative **width % / height %** — that
sizing is palette-only; other dialogs keep their own natural size.

The settings live in `~/.pdf-toolkit/palette.json` and are edited from the palette itself
(**Palette: font size…**, **Palette: opacity %…**, **Palette: toggle borderless**). See
`COMMAND_PALETTE.md` → *Appearance settings* for the ranges, defaults, and the
`PDF_TOOLKIT_PALETTE_FILE` override.

## No flicker

Chrome is applied in the `exec()` override **before** the native window is first shown —
not in `showEvent`. Toggling `FramelessWindowHint` on an already-visible window forces Qt
to destroy and recreate it (a visible flash). Setting it up front bakes it into the window
at creation, so there is no flicker, even with `borderless` on.

## Dialog catalog

| Dialog | File | Base | Used for |
|--------|------|------|----------|
| `FilterListDialog` | `filter_list_dialog.py` | `FilterableListDialog` | Command palette, history, font picker, live search, zoom/outline/placement pickers |
| `ColorPickerDialog` | `color_picker_dialog.py` | `FilterableListDialog` | Text + background + outline color |
| `TextInputDialog` | `text_input_dialog.py` | `BaseDialog` | Multi-line field text (Ctrl+Enter applies) |
| `KeyCaptureDialog` | `key_capture_dialog.py` | `BaseDialog` | Capturing one shortcut chord |
| `FileBrowserDialog` | `file_browser_dialog.py` | `BaseDialog` | Open / save / folder picking (vim-style) — see `FILE_BROWSER.md` |
| `ConfirmDialog` | `confirm_dialog.py` | `FormDialog` | Yes/No and Save/Discard/Cancel confirmations; single-OK alerts |
| `NumberInputDialog` | `number_input_dialog.py` | `FormDialog` | Integer / decimal prompts |
| `TextPromptDialog` | `text_prompt_dialog.py` | `FormDialog` | Single-line text prompts |

The list dialogs (`FilterListDialog`, `ColorPickerDialog`, `TextInputDialog`) are
detailed in `WIDGETS.md`; the rest are below.

## Helper API

Drop-in functions that build the dialog, run it, and return a typed value. They replaced
`QMessageBox.question/information/warning/critical` and
`QInputDialog.getInt/getDouble/getText`.

### Confirmations — `confirm_dialog.py`

```python
confirm(parent, title, text, *, primary, secondary=None, cancel=None,
        default=DialogResult.PRIMARY) -> DialogResult
```

Up to three labelled buttons mapped to `DialogResult.PRIMARY` / `SECONDARY` / `CANCEL`.
Pressing **Enter** triggers the `default` button; **Esc** returns the most cautious
available result (`CANCEL` if present, else `SECONDARY`, else `PRIMARY`).

- Two-button Yes/No — delete page, delete saved fields: `primary=Yes, secondary=No`.
- Three-button — unsaved changes (`Save`/`Discard`/`Cancel`), export overwrite, image
  copy-vs-reference.

### Alerts — `confirm_dialog.py`

```python
show_message(parent, title, text, severity=Severity.INFO)  # INFO | WARNING | ERROR
```

A single-OK alert — the same dialog as `confirm` with one button — used for success,
warning, and error popups. The severity prepends a small prefix to the message.

### Value prompts

```python
prompt_int(parent, title, label, value, minimum, maximum) -> int | None      # number_input_dialog.py
prompt_float(parent, title, label, value, minimum, maximum, decimals=2) -> float | None
prompt_text(parent, title, label, text="", *, select_all=True) -> str | None # text_prompt_dialog.py
```

`None` means cancelled. `prompt_text` returns the trimmed text (or `None` if empty after
trimming); `select_all=False` puts the caret at the end instead of selecting — used by
the export-name prompt, which pre-fills the current file name.

## Adding a new dialog

1. Subclass `FormDialog` (title + message via the constructor).
2. Add the value-editing widget with `self.add_content(widget)`.
3. Add buttons with `self.add_ok_cancel()` (or a custom `QDialogButtonBox` +
   `self.add_buttons(box)`).
4. Expose a thin module-level helper that builds the dialog and returns a typed value via
   `exec_value(dialog, reader)`.

The appearance chrome is applied automatically — nothing to wire. Keep each dialog in its
own file, ≤300 lines.

> Call the helpers **module-qualified** (`confirm_dialog.confirm(...)`,
> `number_input_dialog.prompt_int(...)`) rather than importing the function by name. Tests
> patch them at the module (`monkeypatch.setattr(confirm_dialog, "confirm", …)`), and the
> shared `tests/conftest.py` `silence_dialogs(monkeypatch)` helper relies on that.

## Shared keys

| Key | Action |
|-----|--------|
| **Up / Down** | Move selection in list dialogs (wraps at the ends) |
| **Enter** | Accept — runs the default button / highlighted row |
| **Esc** | Cancel — most cautious result for confirmations |
| **Ctrl+Enter** | Apply in the multi-line `TextInputDialog` (plain Enter = newline) |
