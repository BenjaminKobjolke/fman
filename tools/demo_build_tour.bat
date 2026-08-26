@echo off
REM Join the recorded tour chapters into media/demos/tour/feature-tour.mp4.
REM Record them first: tools\demos_record.bat --demo 3 (4, 5, 6, 7).
REM Needs ffmpeg on PATH. Override the interpreter with FMAN_PYTHON.
setlocal
if not defined FMAN_PYTHON set "FMAN_PYTHON=python"
"%FMAN_PYTHON%" "%~dp0create_media\build_tour.py" %*
