@echo off
setlocal
pushd "%~dp0\.."
call .venv\Scripts\activate.bat
python -m pytest tests\integration -v
set EXITCODE=%ERRORLEVEL%
popd
endlocal & exit /b %EXITCODE%
