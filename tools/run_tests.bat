@echo off
REM Run the whole fman_unittest suite in two processes: test*.py, then the
REM *_test.py files that need their own QApplication. Does not run fman_integrationtest.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\unittest\python;%ROOT%\src\main\resources\base\Plugins\Core
call "%~dp0unittest_with_timeout.bat" discover -v -s "%ROOT%\src\unittest\python" -t "%ROOT%\src\unittest\python" -p "test*.py"
set "TESTRESULT=%ERRORLEVEL%"
call "%~dp0unittest_with_timeout.bat" discover -v -s "%ROOT%\src\unittest\python" -t "%ROOT%\src\unittest\python" -p "*_test.py"
if "%TESTRESULT%"=="0" set "TESTRESULT=%ERRORLEVEL%"
exit /b %TESTRESULT%
