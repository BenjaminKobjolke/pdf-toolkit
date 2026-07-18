@echo off
REM Publish the versioned installer exe built by tools\build_release.bat.
REM The release-tool pipeline signs the installer ([PreSigning]) and uploads it;
REM the FastFileViewer.exe inside was already signed during build_release.
setlocal
call "%~dp0..\.venv\Scripts\activate.bat"
for /f "usebackq delims=" %%i in (`python -m app.release.release_info`) do set "LABEL=%%i"

set "INSTALLER=%~dp0..\releases\windows\FastFileViewer_v%LABEL%.exe"
if not exist "%INSTALLER%" (
    echo [publish_release] Installer not found: %INSTALLER%
    echo [publish_release] Run tools\build_release.bat first.
    exit /b 1
)

cd D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool "%INSTALLER%" "%~dp0publish_settings.ini" --previous-version 0.0.0 --verbose
cd "%~dp0"
