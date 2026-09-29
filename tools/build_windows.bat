cd "%~dp0.."
call python build.py freeze
@set "RESULT=%ERRORLEVEL%"
cd "%~dp0"
@exit /b %RESULT%
