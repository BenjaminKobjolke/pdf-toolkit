@echo off
REM Build a release: run unit tests, build the exe (release_notes bundled),
REM then copy the exe into release\<version>_<build>\.
REM Bump the build number first with tools\build_increment.bat if needed.
REM On success the label is recorded in releases\windows\release_version.txt;
REM publish_release.bat ships that completed build, not the current source label.
setlocal
set "PROJECT_ROOT=%~dp0.."
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"

echo [build_release] Running unit tests...
python -m pytest "%PROJECT_ROOT%\tests\unit" -q
if errorlevel 1 (
    echo [build_release] Tests failed; aborting.
    exit /b 1
)

for /f "usebackq delims=" %%i in (`python -m app.release.release_info`) do set "LABEL=%%i"
if not defined LABEL (
    echo [build_release] Could not read the release label; aborting.
    exit /b 1
)
echo [build_release] Release label: %LABEL%

REM Rebuilding the recorded label overwrites its installer in place, so drop the
REM record first: a failed rebuild must not leave a half-built pair publishable.
set "RECORD=%PROJECT_ROOT%\releases\windows\release_version.txt"
set "RECORDED="
if exist "%RECORD%" set /p "RECORDED="<"%RECORD%"
if "%RECORDED%"=="%LABEL%" del "%RECORD%"

call "%~dp0build_exe.bat"
if errorlevel 1 exit /b 1

echo [build_release] Signing FastFileViewer.exe (network-share signer)...
call uv run --project D:\GIT\BenjaminKobjolke\release-tool python "%~dp0presign_exe.py" "%PROJECT_ROOT%\dist\FastFileViewer\FastFileViewer.exe" "%~dp0publish_settings.ini"
if errorlevel 1 (
    echo [build_release] Signing failed; aborting.
    exit /b 1
)

echo [build_release] Building installer...
if not exist "%PROJECT_ROOT%\releases\windows" mkdir "%PROJECT_ROOT%\releases\windows"
call makensis "%PROJECT_ROOT%\installer\installer.nsi"
if errorlevel 1 (
    echo [build_release] Installer build failed; aborting.
    exit /b 1
)
move /y "%PROJECT_ROOT%\releases\windows\installer.exe" "%PROJECT_ROOT%\releases\windows\FastFileViewer_v%LABEL%.exe" >nul
if errorlevel 1 (
    echo [build_release] Installer rename failed; aborting.
    exit /b 1
)
echo [build_release] Installer: %PROJECT_ROOT%\releases\windows\FastFileViewer_v%LABEL%.exe

set "OUTDIR=%PROJECT_ROOT%\release\%LABEL%"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
robocopy "%PROJECT_ROOT%\dist\FastFileViewer" "%OUTDIR%\FastFileViewer" /mir /njh /njs /ndl /nc /ns >nul
if errorlevel 8 (
    echo [build_release] Copy failed.
    exit /b 1
)
if not exist "%PROJECT_ROOT%\releases\windows\FastFileViewer_v%LABEL%.exe" (
    echo [build_release] Installer missing after build; not recording %LABEL%.
    exit /b 1
)
>"%RECORD%" (echo %LABEL%)
echo [build_release] Recorded completed build %LABEL% in %RECORD%
echo [build_release] Done: %OUTDIR%\FastFileViewer\FastFileViewer.exe
exit /b 0
