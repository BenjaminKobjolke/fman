cd "%~dp0.."
@REM A fman started from target\fman locks the files freeze() replaces.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0close_running_fman.ps1" -Directory "%~dp0..\target\fman" <NUL
@set "RESULT=%ERRORLEVEL%"
@if not "%RESULT%"=="0" goto :done
call python build.py freeze
@set "RESULT=%ERRORLEVEL%"
:done
cd "%~dp0"
@exit /b %RESULT%
