# Application Icon

The GUI window (title-bar / Windows taskbar) and the compiled `dist/pdft-gui.exe`
both use a single icon, derived from one source PNG.

## Pipeline

```
assets/icon.png  ──(tools/png_to_ico.bat)──▶  assets/icon.ico
                                                   │
                          ┌────────────────────────┴────────────────────────┐
                          ▼                                                   ▼
        runtime: app.setWindowIcon(app_icon())              build: pdft-gui.spec icon=
        (app/gui/main.py → app/gui/resources.py)            (embedded in the exe)
```

Windows + PyInstaller require a multi-resolution `.ico` for the exe icon; Qt loads
that same `.ico` at runtime. So the PNG is converted once and reused for both.

## Files

| File | Role |
|------|------|
| `assets/icon.png` | Source art (user-supplied). Square, ≥ 256×256 recommended. |
| `assets/icon.ico` | Generated multi-size icon (16/32/48/64/128/256 px). |
| `tools/png_to_ico.py` | Converter (Pillow). Logs via `logging`; fails fast if the PNG is missing. |
| `tools/png_to_ico.bat` | Wrapper around the converter. |
| `app/gui/resources.py` | `asset_path()` + `app_icon()`. `sys._MEIPASS`-aware so it resolves in both source and frozen runs. |
| `app/gui/main.py` | Calls `app.setWindowIcon(app_icon())` — app-level, so child dialogs inherit it too. |
| `pdft-gui.spec` | `datas=[('assets/icon.ico','assets')]` bundles it; `icon='assets/icon.ico'` embeds it in the exe. |

## Updating the icon

1. Replace `assets/icon.png` with the new art.
2. Run the converter:
   ```bat
   tools\png_to_ico.bat
   ```
   Optional explicit paths: `tools\png_to_ico.bat <src.png> <out.ico>`.
   Defaults are `assets/icon.png` → `assets/icon.ico`.
3. Verify at runtime — `pdft-gui` from source shows the icon in the title-bar and
   Windows taskbar.
4. Rebuild the exe:
   ```bat
   tools\build_exe.bat
   ```
   In Explorer, `dist\pdft-gui.exe` shows the embedded icon; launching it shows the
   window/taskbar icon (confirms the bundled `.ico` resolves via `sys._MEIPASS`).

## Notes

- The spec references `assets/icon.ico`, so `build_exe.bat` fails until the converter
  has produced it. Commit both `assets/icon.png` and `assets/icon.ico` so a clean
  checkout builds without re-running the converter.
- Pillow (`pillow>=10.0,<12.0`) is already a project dependency — no extra install.
