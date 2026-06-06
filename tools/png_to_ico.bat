@echo off
setlocal
set "PROJECT_ROOT=%~dp0.."
echo [png_to_ico] Converting PNG to assets\icon.ico...
"%PROJECT_ROOT%\.venv\Scripts\python.exe" "%PROJECT_ROOT%\tools\png_to_ico.py" %*
if errorlevel 1 (
    echo [png_to_ico] Conversion failed.
    exit /b 1
)
echo [png_to_ico] Done.
exit /b 0
