@echo off
setlocal
set "PROJECT_ROOT=%~dp0.."
echo [build_exe] Building dist\FastFileViewer\FastFileViewer.exe (onedir, windowed)...
"%PROJECT_ROOT%\.venv\Scripts\pyinstaller.exe" "%PROJECT_ROOT%\FastFileViewer.spec" --noconfirm --distpath "%PROJECT_ROOT%\dist" --workpath "%PROJECT_ROOT%\build"
if errorlevel 1 (
    echo [build_exe] Build failed.
    exit /b 1
)
echo [build_exe] Done: %PROJECT_ROOT%\dist\FastFileViewer\FastFileViewer.exe
exit /b 0
