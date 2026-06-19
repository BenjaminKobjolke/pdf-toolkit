@echo off
setlocal
pushd "%~dp0\.."
call .venv\Scripts\activate.bat
python -m app.release.release_info
set EXITCODE=%ERRORLEVEL%
popd
endlocal & exit /b %EXITCODE%
