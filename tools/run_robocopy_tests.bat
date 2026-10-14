@echo off
REM Run only the Robocopy plugin's own unit tests.
setlocal
REM Tickets Watcher starts this with its own venv first on PATH. fman has no
REM venv: fbs_runtime and PyQt5 live in the system python, so drop the inherited one.
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\main\resources\base\Plugins\Robocopy
python -m unittest discover -v ^
	-s "%ROOT%\src\main\resources\base\Plugins\Robocopy\robocopy_plugin\tests"
exit /b %ERRORLEVEL%
