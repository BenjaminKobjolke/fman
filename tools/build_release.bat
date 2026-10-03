@echo off
REM Build the signed release installer (target\fmanSetup.exe) and record its label.
REM Called by release_create.bat (release-tool create), which owns the build bump,
REM translation and rollback - this bat only builds the version that is already set.
REM Close any running fman.exe first: freeze() cannot replace target\fman\ under it.
setlocal

REM release-tool starts this bat through "uv run", whose venv comes first on PATH.
REM fman has no venv: fbs lives in the system python, so drop the inherited one.
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="

set "ROOT=%~dp0.."
set "RECORD=%ROOT%\target\release_version.txt"

REM The build replaces target\fmanSetup.exe in place. Drop the old record first, so
REM a failed build cannot leave a stale label paired with a half-built installer.
if exist "%RECORD%" del "%RECORD%"

cd /d "%ROOT%"
call python build.py release_build
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto :done

if not exist "target\fmanSetup.exe" (
    echo ERROR: build reported success but target\fmanSetup.exe is missing.
    set "RESULT=1"
    goto :done
)

REM Recorded only now: github_release.bat publishes this label, not whatever
REM build_version.txt holds by the time it runs.
python tools\release\build_number.py label > "%RECORD%"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" del "%RECORD%"

:done
cd /d "%~dp0"
endlocal & exit /b %RESULT%
