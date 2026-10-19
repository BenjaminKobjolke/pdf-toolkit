@echo off
REM Publish the installer of the last COMPLETED build of tools\build_release.bat.
REM The release-tool pipeline signs the installer ([PreSigning]) and uploads it;
REM the FastFileViewer.exe inside was already signed during build_release.
REM
REM   %1  previous ONLINE label: names the remote archive folder versions\<label>\.
REM       Default: tools\previous_version.txt (written by tools\release_create.bat).
REM   %2  label of the build to ship (retry an older build, e.g. 0.2.0_4).
REM       Default: releases\windows\release_version.txt (written by build_release).
REM Never derived from the source version: the counter may have moved on since.
setlocal
if not exist "%~dp0publish_settings.ini" (
    echo [publish_release] Missing %~dp0publish_settings.ini - copy publish_settings_example.ini.
    exit /b 1
)

set "PREV=%~1"
if not defined PREV if exist "%~dp0previous_version.txt" set /p "PREV="<"%~dp0previous_version.txt"
if not defined PREV (
    echo [publish_release] Previous online version unknown: pass it as %%1 or create tools\previous_version.txt.
    exit /b 1
)

set "LABEL=%~2"
set "RECORD=%~dp0..\releases\windows\release_version.txt"
if not defined LABEL if exist "%RECORD%" set /p "LABEL="<"%RECORD%"
if not defined LABEL (
    echo [publish_release] No completed build recorded in %RECORD%.
    echo [publish_release] Run tools\build_release.bat first, or pass the label as %%2.
    exit /b 1
)

set "INSTALLER=%~dp0..\releases\windows\FastFileViewer_v%LABEL%.exe"
if not exist "%INSTALLER%" (
    echo [publish_release] Installer not found: %INSTALLER%
    exit /b 1
)
echo [publish_release] Shipping %LABEL% ^(previous online: %PREV%^)

REM Upload under a stable filename (constant download URL); the versioned file
REM stays local as the version stamp. release-tool archives the previous remote
REM FastFileViewer.exe into versions\<PREV>\ before replacing it.
set "ARTIFACT=%~dp0..\releases\windows\FastFileViewer.exe"
copy /y "%INSTALLER%" "%ARTIFACT%" >nul
if errorlevel 1 (
    echo [publish_release] Copy to %ARTIFACT% failed.
    exit /b 1
)
fc /b "%INSTALLER%" "%ARTIFACT%" >nul
if errorlevel 1 (
    echo [publish_release] %ARTIFACT% does not match %INSTALLER%.
    exit /b 1
)

if not defined RELEASE_TOOL_CMD set "RELEASE_TOOL_CMD=uv run python -m release_tool"
cd /d D:\GIT\BenjaminKobjolke\release-tool
call %RELEASE_TOOL_CMD% "%ARTIFACT%" "%~dp0publish_settings.ini" --previous-version "%PREV%" --verbose
set "PUBLISH_EXIT_CODE=%ERRORLEVEL%"
cd /d "%~dp0"
endlocal & exit /b %PUBLISH_EXIT_CODE%
