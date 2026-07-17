@echo off
setlocal
REM Registers pdf-toolkit's GUI viewer as an available PDF handler for the
REM current user (HKCU, no admin needed). Windows 11 does not allow any tool to
REM silently force the *default* app, so after running this you set the default
REM once via the UI (see the printed instructions).

set "PROGID=pdf-toolkit.Viewer"
set "VBS=%~dp0FastFileViewer.vbs"

if not exist "%VBS%" (
    echo [register] launcher not found: %VBS%
    exit /b 1
)

echo [register] creating ProgID %PROGID% ...
reg add "HKCU\Software\Classes\%PROGID%" /ve /t REG_SZ /d "PDF (pdf-toolkit viewer)" /f >nul
reg add "HKCU\Software\Classes\%PROGID%\DefaultIcon" /ve /t REG_SZ /d "%SystemRoot%\System32\shell32.dll,1" /f >nul
reg add "HKCU\Software\Classes\%PROGID%\shell\open\command" /ve /t REG_SZ /d "wscript.exe \"%VBS%\" \"%%1\"" /f >nul

echo [register] adding %PROGID% to the .pdf 'Open with' list ...
reg add "HKCU\Software\Classes\.pdf\OpenWithProgids" /v "%PROGID%" /t REG_NONE /d "" /f >nul

echo.
echo [register] done.
echo.
echo Final step (Windows blocks silent default changes):
echo   1) Right-click any .pdf -^> Open with -^> Choose another app
echo   2) Pick "PDF (pdf-toolkit viewer)"
echo   3) Tick "Always use this app", then OK
echo.
echo Undo with: FastFileViewer_unregister.bat
exit /b 0
