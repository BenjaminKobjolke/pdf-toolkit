@echo off
setlocal
pushd "%~dp0"

echo [update] Upgrading lockfile...
uv lock --upgrade
if errorlevel 1 goto :fail

echo [update] Syncing dependencies...
uv sync --all-extras
if errorlevel 1 goto :fail

call .venv\Scripts\activate.bat

echo [update] ruff check...
python -m ruff check .
if errorlevel 1 goto :fail

echo [update] ruff format check...
python -m ruff format --check .
if errorlevel 1 goto :fail

echo [update] mypy...
python -m mypy
if errorlevel 1 goto :fail

echo [update] tests...
python -m pytest tests -v
if errorlevel 1 goto :fail

popd
endlocal
exit /b 0

:fail
popd
endlocal
exit /b 1
