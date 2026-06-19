@echo off
setlocal
pushd "%~dp0\.."
call .venv\Scripts\activate.bat
python -m app.release.build_number increment
set EXITCODE=%ERRORLEVEL%
popd
endlocal & exit /b %EXITCODE%
