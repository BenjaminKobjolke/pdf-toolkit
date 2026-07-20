# Application Icon

The GUI window (title-bar / Windows taskbar) and the compiled
`dist/FastFileViewer/FastFileViewer.exe` both use a single icon, derived from one
source PNG.

## Pipeline

```
tools/create_media/create_app_icon.bat  ──(ai-image-creator, optional)──▶  assets/icon.png

assets/icon.png  ──(tools/png_to_ico.bat)──▶  assets/icon.ico
                                                   │
                          ┌────────────────────────┴────────────────────────┐
                          ▼                                                   ▼
        runtime: app.setWindowIcon(app_icon())              build: FastFileViewer.spec icon=
        (app/gui/main.py → app/gui/resources.py)            (embedded in the exe)
```

Windows + PyInstaller require a multi-resolution `.ico` for the exe icon; Qt loads
that same `.ico` at runtime. So the PNG is converted once and reused for both.

## Files

| File | Role |
|------|------|
| `assets/icon.png` | Source art (AI-generated or user-supplied). Square, ≥ 256×256 recommended. |
| `assets/icon.ico` | Generated multi-size icon (16/32/48/64/128/256 px). |
| `tools/create_media/create_app_icon.json` | Image-generation request: prompt (pure-white monochrome line icon, square document + lightning bolt), reference images, output path/size. |
| `tools/create_media/create_app_icon.bat` | Regenerates `assets/icon.png` via the `ai-image-creator` repo, then calls `png_to_ico.bat`. |
| `tools/png_to_ico.py` | Converter (Pillow). Logs via `logging`; fails fast if the PNG is missing. |
| `tools/png_to_ico.bat` | Wrapper around the converter. |
| `app/gui/resources.py` | `asset_path()` + `app_icon()`. `sys._MEIPASS`-aware so it resolves in both source and frozen runs. |
| `app/gui/main.py` | Calls `app.setWindowIcon(app_icon())` — app-level, so child dialogs inherit it too. |
| `FastFileViewer.spec` | `datas=[('assets/icon.ico','assets')]` bundles it; `icon='assets/icon.ico'` embeds it in the exe. |

## Regenerating the art (AI)

Requires `D:\GIT\BenjaminKobjolke\ai-image-creator` cloned and installed, with its
`.env` holding a valid `OPENAI_API_KEY` (the key stays there — never in this repo).

```bat
tools\create_media\create_app_icon.bat
```

This generates `assets/icon.png` from the prompt in `create_app_icon.json` and then
converts it to `assets/icon.ico` in one go. To change the design, edit the `prompt`
in the JSON and rerun. The `reference_images` resolve relative to the
ai-image-creator directory (`examples/media/icon_*.png` pin the white line-icon style).

The model sometimes ignores the "pure white" instruction and draws black strokes.
Deterministic fix instead of re-rolling — recolor keeping alpha, then reconvert:

```bat
uv run python -c "from PySide6.QtGui import QImage, qRgba, qAlpha; p = r'assets\icon.png'; img = QImage(p).convertToFormat(QImage.Format_ARGB32); [img.setPixel(x, y, qRgba(255, 255, 255, qAlpha(img.pixel(x, y)))) for y in range(img.height()) for x in range(img.width())]; img.save(p)"
tools\png_to_ico.bat
```

## Updating the icon (manual art)

1. Replace `assets/icon.png` with the new art.
2. Run the converter:
   ```bat
   tools\png_to_ico.bat
   ```
   Optional explicit paths: `tools\png_to_ico.bat <src.png> <out.ico>`.
   Defaults are `assets/icon.png` → `assets/icon.ico`.
3. Verify at runtime — `FastFileViewer` from source shows the icon in the title-bar and
   Windows taskbar.
4. Rebuild the exe:
   ```bat
   tools\build_exe.bat
   ```
   In Explorer, `dist\FastFileViewer\FastFileViewer.exe` shows the embedded icon;
   launching it shows the window/taskbar icon (confirms the bundled `.ico` resolves
   via `sys._MEIPASS`).

## Notes

- The spec references `assets/icon.ico`, so `build_exe.bat` fails until the converter
  has produced it. Commit both `assets/icon.png` and `assets/icon.ico` so a clean
  checkout builds without re-running the converter.
- Pillow (`pillow>=10.0,<12.0`) is already a project dependency — no extra install.
- The icon is pure white on transparent: crisp on dark taskbars/title bars, but
  near-invisible on light backgrounds (e.g. Explorer's white view). Regenerate with a
  colored prompt if that becomes a problem.
