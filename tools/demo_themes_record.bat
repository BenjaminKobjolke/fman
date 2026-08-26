@echo off
REM Record one still per installed theme and join them into the README's
REM media/demos/themes/themes.gif. One command, because the two halves are
REM useless apart: the recording writes no video at all.
REM
REM Prereqs: pip install -r requirements/windows-debug.txt, and ffmpeg on PATH.
REM Override the interpreter with FMAN_PYTHON.
setlocal
set "STILLS=%~dp0..\media\demos\themes"

REM Wipe first: the GIF is built from whatever PNGs are in that folder, so a
REM still left over from a theme that no longer exists would stay in it.
if exist "%STILLS%" del /q "%STILLS%\*.png"

set "FMAN_NO_PAUSE=1"
call "%~dp0demos_record.bat" --demo 2 || exit /b 1

if not defined FMAN_PYTHON set "FMAN_PYTHON=python"
"%FMAN_PYTHON%" "%~dp0create_media\build_themes.py"
pause
