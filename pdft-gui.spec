# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: builds dist/pdft-gui.exe (onefile, windowed).
# Build via tools/build_exe.bat. PySide6 + pymupdf bundle through built-in hooks.

a = Analysis(
    ['app/cli/gui.py'],
    pathex=['.'],  # project root so `import app...` resolves
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pdft-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # no console window (matches pythonw behavior)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
