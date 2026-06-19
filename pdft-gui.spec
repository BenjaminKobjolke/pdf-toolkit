# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: builds dist/FastPDFToolkit.exe (onefile, windowed).
# Build via tools/build_exe.bat. PySide6 + pymupdf bundle through built-in hooks.

from PyInstaller.utils.hooks import copy_metadata

# release_notes/ + build_version.txt travel inside the exe so the in-app
# Release Notes view works from a standalone build; copy_metadata bundles the
# package dist-info so importlib.metadata can read the version when frozen.
datas = [
    ('assets/icon.ico', 'assets'),
    ('release_notes', 'release_notes'),
    ('build_version.txt', '.'),
]
datas += copy_metadata('pdf-toolkit')

a = Analysis(
    ['app/cli/gui.py'],
    pathex=['.'],  # project root so `import app...` resolves
    binaries=[],
    datas=datas,
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
    name='FastPDFToolkit',
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
    icon='assets/icon.ico',
)
