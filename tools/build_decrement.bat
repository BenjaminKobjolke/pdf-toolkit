@echo off
setlocal
pushd "%~dp0\.."
call .venv\Scripts\activate.bat
python -m app.release.build_number decrement
set EXITCODE=%ERRORLEVEL%
popd
endlocal & exit /b %EXITCODE%
