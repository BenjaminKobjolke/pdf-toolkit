@echo off
setlocal
REM Removes the pdf-toolkit GUI viewer PDF-handler registration created by
REM pdft_gui_register.bat. If you had set it as the Windows default, also reset
REM the default to another app via Settings -> Apps -> Default apps.

set "PROGID=pdf-toolkit.Viewer"

echo [unregister] removing %PROGID% from the .pdf 'Open with' list ...
reg delete "HKCU\Software\Classes\.pdf\OpenWithProgids" /v "%PROGID%" /f >nul 2>nul

echo [unregister] removing ProgID %PROGID% ...
reg delete "HKCU\Software\Classes\%PROGID%" /f >nul 2>nul

echo [unregister] done.
exit /b 0
