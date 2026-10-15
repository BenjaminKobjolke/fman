@echo off
REM Run the tests of fman's "close for build" countdown (build_shutdown.py).
REM Excluded from `python build.py test` - hence the *_test.py name, which its
REM discovery does not match - because they need a QApplication of their own
REM and leftover Qt state is what makes that suite hang. See CLAUDE.md.
REM Offscreen, so no window appears.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\unittest\python
set QT_QPA_PLATFORM=offscreen
call "%~dp0unittest_with_timeout.bat" -v fman_unittest.impl.build_shutdown_test
set TESTRESULT=%ERRORLEVEL%
exit /b %TESTRESULT%
