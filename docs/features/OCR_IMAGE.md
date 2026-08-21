# OCR image (extract text)

The viewer can recognize the **text in an image document** (PNG, JPG, GIF, BMP,
TIFF, WEBP, PSD) using the **Windows built-in OCR engine** and hand you the
result — either on the **clipboard** or saved as a **`.txt` file next to the
image**.

OCR applies to **image formats only**. PDFs and text documents keep their
existing text-extraction commands (**Copy all text from current page**).

## Running it

Open the command palette (**Ctrl+Shift+P**) with an image open and run:

| Command | Effect |
|---------|--------|
| **OCR image (extract text)…** | Recognize the image's text, then pick what to do with it. |

After recognition a keyboard-first picker offers two choices:

- **Copy text to clipboard** — puts the recognized text on the clipboard.
- **Save as `<name>.txt`** — writes the text next to the image, same filename
  with the extension swapped to `.txt` (`scan.png` → `scan.txt`). If the file
  already exists, a **Yes/No overwrite confirmation** appears first. The write
  is atomic (temp file + replace).

**Esc** in the picker or the confirmation cancels with no side effects.

The command is **shown only for image documents** and can be bound to a keyboard
shortcut via **Configure keyboard shortcuts…** (see `../CONFIGURE_SHORTCUTS.md`).

## Details & limitations

- **Reads the file on disk** — unsaved in-session rotations/flips are **not**
  reflected in the OCR result. Save first if orientation matters.
- **Thumbnails view**: the command targets the **selected thumbnail's** file on
  disk, like the other file commands (see `../THUMBNAIL_VIEW.md`).
- **Animated GIF / multi-frame TIFF**: only the **first frame** is recognized.
- **No text found** → a status message; nothing is copied or written.
- **Windows only**: recognition uses the OS `Windows.Media.Ocr` engine (via the
  winrt projection packages, installed on Windows only). On other platforms — or
  if the required OCR language pack is missing — the command reports that OCR is
  unavailable instead of failing silently.

## Language

By default the engine picks the recognition language **automatically from your
Windows profile languages**. To override it, run:

| Command | Effect |
|---------|--------|
| **OCR: language…** | Pick **Automatic (Windows profile languages)** or one of the **installed Windows OCR language packs** (e.g. *German (Germany) (de-DE)*). |

The choice is **remembered across sessions** (sqlite settings backend, entry
**"OCR language"**) and applies to every following OCR run. Reset it via
**Remembered settings…** (see `../REMEMBERED_SETTINGS.md`). Additional languages
are installed through Windows Settings → Language (each language pack can
include OCR support).

## How it fits together

- `app/ocr/provider.py` — the engine seam: `OcrProvider` (abstract base:
  `recognize(path, language)`, `available_languages()`, `is_available()`),
  `WindowsOcrProvider` (winrt interop), `default_provider()`. Future engines
  (Tesseract, …) implement `OcrProvider` and swap in via `default_provider`.
- `app/config/ocr_settings.py` — persisted `OcrSettings.language` (`""` =
  automatic); `app/gui/ocr_language_controller.py` — the language picker.
- `app/gui/ocr_actions.py` — the command flow: availability check → wait-cursor
  recognition → copy-or-save picker → clipboard / atomic `.txt` write.
- `app/gui/ocr_strings.py` — all user-facing strings.
- `app/gui/view_commands.py` — the palette entry (`OCR_IMAGE`,
  image-formats-only, retargets to the grid selection).
- `app/gui/window_builder_files.py` — wires `OcrActions` with the
  effective-target source resolver.

Covered by `tests/unit/test_ocr_provider.py` and
`tests/integration/test_ocr_image_palette.py`.
