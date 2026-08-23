@echo off
REM Deletes the cached libmpv-2.dll (see core/libmpv.py) so the next video
REM opened in fman re-downloads it from scratch. For manually testing the
REM first-use download path (progress dialog, hash check, extraction).
setlocal
set CACHE_DIR=%APPDATA%\fman\Local\libmpv
if exist "%CACHE_DIR%" (
	rmdir /s /q "%CACHE_DIR%"
	echo Deleted %CACHE_DIR%
) else (
	echo %CACHE_DIR% does not exist - nothing to delete.
)
endlocal
