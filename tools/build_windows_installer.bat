cd "%~dp0.."
call "%~dp0find_build_python.bat"
@set "RESULT=%ERRORLEVEL%"
@if not "%RESULT%"=="0" goto :done
call "%FMAN_PYTHON%" build.py installer
@set "RESULT=%ERRORLEVEL%"
:done
cd "%~dp0"
@exit /b %RESULT%
