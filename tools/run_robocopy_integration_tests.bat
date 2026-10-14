@echo off
REM Runs real robocopy.exe; excluded from unit discovery because AV/EDR can stall child processes.
setlocal
REM Tickets Watcher starts this with its own venv first on PATH. fman has no
REM venv: fbs_runtime and PyQt5 live in the system python, so drop the inherited one.
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\main\resources\base\Plugins\Robocopy
python -m unittest discover -v -p "robocopy_integration_test.py" ^
	-s "%ROOT%\src\main\resources\base\Plugins\Robocopy\robocopy_plugin\tests"
exit /b %ERRORLEVEL%
