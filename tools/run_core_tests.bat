@echo off
REM Run only the Core plugin's own tests (core/tests/**), skipping the
REM fbs-default fman_unittest/fman_integrationtest suites and the isolated
REM zip tests (see run_zip_tests.bat). Fast, reliable feedback loop for
REM day-to-day feature work in the Core plugin.
setlocal
REM Tickets Watcher starts this with its own venv first on PATH. fman has no
REM venv: fbs_runtime and PyQt5 live in the system python, so drop the inherited one.
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python
python -m unittest discover -v ^
	-s "%ROOT%\src\main\resources\base\Plugins\Core\core" ^
	-t "%ROOT%\src\main\resources\base\Plugins\Core"
exit /b %ERRORLEVEL%
