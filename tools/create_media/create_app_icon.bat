@echo off
REM Generate the app icon via the ai-image-creator project, then convert the PNG
REM to this project's icon format. Needs ai-image-creator's .env OpenAI key set.
setlocal
set PROJECT=D:\GIT\BenjaminKobjolke\pdf-toolkit
set AIC=D:\GIT\BenjaminKobjolke\ai-image-creator

REM cd so uv resolves ai-image-creator AND the JSON's relative reference_images resolve.
cd /d "%AIC%"
call "%AIC%\start.bat" "%PROJECT%\tools\create_media\create_app_icon.json"
if errorlevel 1 exit /b 1

REM Convert PNG -> .ico with the project's own PySide6 (no extra dep).
uv run --project "%PROJECT%" python -c "from PySide6.QtGui import QImage; QImage(r'%PROJECT%\assets\icon.png').save(r'%PROJECT%\assets\icon.ico')"
