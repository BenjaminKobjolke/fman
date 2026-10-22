@echo off
REM Bump the version in base.json and print the new value.
python "%~dp0release\build_number.py" increment
exit /b %ERRORLEVEL%
