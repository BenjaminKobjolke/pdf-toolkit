REM @echo off
cd D:\GIT\BenjaminKobjolke\release-tool

call uv run python -m release_tool "%~dp0..\dist\FastPDFToolkit.exe" "%~dp0publish_settings.ini" --previous-version 0.0.0 --verbose

cd "%~dp0"
