@echo off
setlocal
if not exist "%~dp0publish_settings.ini" (
  echo ERROR: "%~dp0publish_settings.ini" is missing. Copy publish_settings_example.ini and configure it.
  exit /b 1
)
if not exist "D:\GIT\BenjaminKobjolke\release-tool\ftp_profiles.ini" (
  echo ERROR: "D:\GIT\BenjaminKobjolke\release-tool\ftp_profiles.ini" is missing. Copy examples\ftp_profiles.ini and add the FTP profile.
  exit /b 1
)
cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool create "%~dp0release_create.ini" --project-root "%~dp0.." %*
set "RELEASE_EXIT_CODE=%ERRORLEVEL%"
cd /d "%~dp0"
endlocal & exit /b %RELEASE_EXIT_CODE%
