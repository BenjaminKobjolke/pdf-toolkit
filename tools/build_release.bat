@echo off
REM Build a release: run unit tests, build the exe (release_notes bundled),
REM then copy the exe into release\<version>_<build>\.
REM Bump the build number first with tools\build_increment.bat if needed.
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
echo [build_release] Release label: %LABEL%

call "%~dp0build_exe.bat"
if errorlevel 1 exit /b 1

set "OUTDIR=%PROJECT_ROOT%\release\%LABEL%"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
robocopy "%PROJECT_ROOT%\dist\FastFileViewer" "%OUTDIR%\FastFileViewer" /mir /njh /njs /ndl /nc /ns >nul
if errorlevel 8 (
    echo [build_release] Copy failed.
    exit /b 1
)
echo [build_release] Done: %OUTDIR%\FastFileViewer\FastFileViewer.exe
exit /b 0
