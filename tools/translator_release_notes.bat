@echo off
REM Generate non-English release-notes JSON from each en.json under release_notes/.
REM Uses the shared GPT-json-translator tool; --translate-recursive walks every
REM release_notes/<version>_<build>/en.json and writes the other locales beside it.
set "NOTES_DIR=%~dp0..\release_notes"
d:
cd "d:\GIT\BenjaminKobjolke\GPT-json-translator"

call .\.venv\Scripts\python.exe json_translator.py "%NOTES_DIR%" --translate-recursive="en.json"

REM %ERRORLEVEL% expands when this line is parsed, so the tool's exit code survives the cd.
cd %~dp0 & exit /b %ERRORLEVEL%
