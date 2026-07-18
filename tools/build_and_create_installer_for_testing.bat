@echo off
REM Build the exe and NSIS installer for local testing — no code signing, no tests.
REM Output gets an _unsigned suffix so it never gets confused with release artifacts.
setlocal
set "PROJECT_ROOT=%~dp0.."
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"

for /f "usebackq delims=" %%i in (`python -m app.release.release_info`) do set "LABEL=%%i"
echo [build_installer_testing] Release label: %LABEL%

call "%~dp0build_exe.bat"
if errorlevel 1 exit /b 1

echo [build_installer_testing] Building installer (unsigned)...
if not exist "%PROJECT_ROOT%\releases\windows" mkdir "%PROJECT_ROOT%\releases\windows"
call makensis "%PROJECT_ROOT%\installer\installer.nsi"
if errorlevel 1 (
    echo [build_installer_testing] Installer build failed; aborting.
    exit /b 1
)
move /y "%PROJECT_ROOT%\releases\windows\installer.exe" "%PROJECT_ROOT%\releases\windows\FastFileViewer_v%LABEL%_unsigned.exe" >nul
echo [build_installer_testing] Installer: %PROJECT_ROOT%\releases\windows\FastFileViewer_v%LABEL%_unsigned.exe
exit /b 0
