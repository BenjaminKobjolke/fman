@echo off
REM Publish the fman GitHub Release for the last-shipped label (reuses release-tool GitHubPublisher).
REM Usage: github_release.bat
REM Run AFTER a signed target\fmanSetup.exe exists and the v<version> tag has been
REM pushed (e.g. via `python build.py release`). Requires the gh CLI, authenticated
REM once via `gh auth login`. Idempotent: re-run re-uploads the asset (--clobber).
setlocal

for /f %%L in ('python "%~dp0release\build_number.py" label') do set "LABEL=%%L"
if not defined LABEL (
    echo ERROR: could not compute release label.
    exit /b 1
)

REM LABEL is "<version>_<build>" (version has dots, never underscores) -> the
REM first underscore always splits version from build.
for /f "tokens=1,* delims=_" %%A in ("%LABEL%") do set "VERSION=%%A"
set "TAG=v%VERSION%"

for %%I in ("%~dp0..\target\fmanSetup.exe") do set "ASSET=%%~fI"
for %%I in ("%~dp0..\release_notes\%LABEL%\en.json") do set "NOTES=%%~fI"

if not exist "%ASSET%" (
    echo ERROR: signed installer not found: %ASSET%
    exit /b 1
)
if not exist "%NOTES%" (
    echo ERROR: release notes not found: %NOTES%
    exit /b 1
)

REM --repo is mandatory: cwd is release-tool's checkout, so gh would otherwise
REM infer release-tool's own remote instead of fman's.
cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool github-release "%TAG%" "%ASSET%" --repo BenjaminKobjolke/fman --notes-json "%NOTES%" --title "fman %VERSION%"
if errorlevel 1 (
    echo ERROR: GitHub Release publish failed for %TAG%
    exit /b 1
)
echo Published GitHub Release: %TAG%
endlocal
exit /b 0
