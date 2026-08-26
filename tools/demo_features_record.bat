@echo off
REM Record the standalone feature clips and build the README's GIFs from them,
REM in one command - the mp4s are gitignored intermediates, so recording them
REM without building the GIFs leaves nothing committable behind.
REM
REM These are NOT tour chapters: tools\demo_build_tour.bat joins every tour-*
REM demo, and these are named feature-* precisely so they stay out of the
REM README's hero video. See docs/DEMOS.md.
REM
REM Prereqs: pip install -r requirements/windows-debug.txt, and ffmpeg on PATH.
REM Override the interpreter with FMAN_PYTHON.
REM
REM Before recording: close always-on-top widgets. The capture is a screen
REM region, so anything drawn over fman is burned into every frame. Demo 8 also
REM records a Go to suggestion list - check the take for private paths.
setlocal

set "FMAN_NO_PAUSE=1"
call "%~dp0demos_record.bat" --demo 8 || exit /b 1
call "%~dp0demos_record.bat" --demo 9 || exit /b 1

call "%~dp0demo_build_feature_gifs.bat" || exit /b 1
pause
