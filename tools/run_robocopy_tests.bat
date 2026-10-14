@echo off
REM Run only the Robocopy plugin's own unit tests.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\main\resources\base\Plugins\Robocopy
call "%~dp0unittest_with_timeout.bat" discover -v ^
	-s "%ROOT%\src\main\resources\base\Plugins\Robocopy\robocopy_plugin\tests"
exit /b %ERRORLEVEL%
