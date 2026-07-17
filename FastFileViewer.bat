@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%PROJECT_ROOT%"
REM pythonw.exe = no console window; start = detach so this bat (and any console
REM it was launched from) returns immediately instead of waiting for the viewer.
start "FastFileViewer" "%PROJECT_ROOT%.venv\Scripts\pythonw.exe" -m app.cli.gui %*
exit /b 0
