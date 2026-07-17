REM @echo off
cd D:\GIT\BenjaminKobjolke\release-tool

powershell -NoProfile -Command "Compress-Archive -Path '%~dp0..\dist\FastFileViewer\*' -DestinationPath '%~dp0..\dist\FastFileViewer.zip' -Force"

call uv run python -m release_tool "%~dp0..\dist\FastFileViewer.zip" "%~dp0publish_settings.ini" --previous-version 0.0.0 --verbose

cd "%~dp0"
