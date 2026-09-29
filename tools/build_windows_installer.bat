cd "%~dp0.."
call python build.py installer
@set "RESULT=%ERRORLEVEL%"
cd "%~dp0"
@exit /b %RESULT%
