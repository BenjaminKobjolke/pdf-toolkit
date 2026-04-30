@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%PROJECT_ROOT%"
"%PROJECT_ROOT%.venv\Scripts\python.exe" -m app.cli.delete_pages %*
exit /b %ERRORLEVEL%
