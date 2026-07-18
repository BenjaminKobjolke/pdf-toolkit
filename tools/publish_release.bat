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

REM Upload under a stable filename (constant download URL); the versioned file
REM stays local as the version stamp. release-tool archives the previous remote
REM FastFileViewer.exe into versions\<--previous-version>\ before replacing it,
REM so update --previous-version to the last SHIPPED label when cutting a release.
set "ARTIFACT=%~dp0..\releases\windows\FastFileViewer.exe"
copy /y "%INSTALLER%" "%ARTIFACT%" >nul

cd D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool "%ARTIFACT%" "%~dp0publish_settings.ini" --previous-version 0.0.0 --verbose
cd "%~dp0"
