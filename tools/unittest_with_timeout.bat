@echo off
setlocal
REM Shared entry point for run_*_tests.bat commands.
REM Tickets Watcher starts this with its own venv first on PATH. fman has no
REM venv: fbs_runtime and PyQt5 live in the system python, so drop the inherited one.
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="
set QT_QPA_PLATFORM=offscreen
python "%~dp0unittest_with_timeout.py" %*
exit /b %ERRORLEVEL%
