@echo off
REM Run only the Core plugin's own tests (core/tests/**), skipping the
REM fbs-default fman_unittest/fman_integrationtest suites and the isolated
REM zip tests (see run_zip_tests.bat). Fast, reliable feedback loop for
REM day-to-day feature work in the Core plugin.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python
call "%~dp0unittest_with_timeout.bat" discover -v ^
	-s "%ROOT%\src\main\resources\base\Plugins\Core\core" ^
	-t "%ROOT%\src\main\resources\base\Plugins\Core"
exit /b %ERRORLEVEL%
