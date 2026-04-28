@echo off
setlocal
pushd "%~dp0"

where uv >nul 2>&1
if errorlevel 1 (
    echo [install] uv is not installed. See https://docs.astral.sh/uv/
    popd
    endlocal
    exit /b 1
)

echo [install] Syncing dependencies...
uv sync --all-extras
if errorlevel 1 goto :fail

echo [install] Running unit tests...
call .venv\Scripts\activate.bat
python -m pytest tests\unit -v
if errorlevel 1 goto :fail

popd
endlocal
exit /b 0

:fail
popd
endlocal
exit /b 1
