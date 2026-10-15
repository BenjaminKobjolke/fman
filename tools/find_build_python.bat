@echo off
REM Select the first Python on PATH that has fbs. The watcher and uv can stack venvs.
set "FMAN_PYTHON="
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined FMAN_PYTHON (
        call "%%P" -c "import fbs" >nul 2>&1
        if not errorlevel 1 set "FMAN_PYTHON=%%P"
    )
)
if defined FMAN_PYTHON exit /b 0
echo ERROR: no python on PATH can import fbs - install fbs into the system python.
exit /b 1
