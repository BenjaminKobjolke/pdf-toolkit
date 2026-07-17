@echo off
setlocal
REM Removes the FastFileViewer file-type associations created by
REM FastFileViewer_register.bat or the GUI's "File type associations..."
REM command. If you had set it as a Windows default, also reset the default
REM via Settings -> Apps -> Default apps.

pushd "%~dp0"
uv run python -m app.os_integration.file_association unregister
set "RC=%ERRORLEVEL%"
popd
if %RC% neq 0 (
    echo [unregister] failed - see message above.
    exit /b %RC%
)
echo [unregister] done.
exit /b 0
