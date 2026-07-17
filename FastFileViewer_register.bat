@echo off
setlocal
REM Associates FastFileViewer with all supported file types for the current
REM user (HKCU, no admin). Thin wrapper over the Python module the GUI's
REM "File type associations..." command uses - see docs/FILE_ASSOCIATIONS.md.
REM Windows blocks silent *default* changes; finish via right-click a file ->
REM Open with -> FastFileViewer -> tick "Always", or the Default Apps page.

pushd "%~dp0"
uv run python -m app.os_integration.file_association register
set "RC=%ERRORLEVEL%"
popd
if %RC% neq 0 (
    echo [register] failed - see message above.
    exit /b %RC%
)
echo [register] done. Undo with: FastFileViewer_unregister.bat
exit /b 0
