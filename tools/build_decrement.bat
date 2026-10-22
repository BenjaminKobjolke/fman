@echo off
REM Restore the version from the current Git commit and print it.
python "%~dp0release\build_number.py" decrement
exit /b %ERRORLEVEL%
