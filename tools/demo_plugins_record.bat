@echo off
REM Record the plugin clips and build the README's GIFs from them, in one
REM command - the mp4s are gitignored intermediates, so recording them without
REM building the GIFs leaves nothing committable behind.
REM
REM PREREQ THE OTHER DEMOS DO NOT HAVE: the plugin being filmed must be
REM installed under %APPDATA%\fman\Plugins\User. The demo profile wipes its
REM Plugins folder every run, and run_fman_demo.bat seeds the one plugin under
REM test back in from there - it aborts if that copy is missing, because a
REM plugin-free take looks perfectly fine and shows nothing.
REM
REM These are NOT tour chapters and NOT feature clips: tools\demo_build_tour.bat
REM joins every tour-* demo, and plugin-* keeps these out of both the hero video
REM and the feature index. See docs/DEMOS_PLUGINS.md.
REM
REM Other prereqs: pip install -r requirements/windows-debug.txt, ffmpeg on PATH.
REM Override the interpreter with FMAN_PYTHON.
REM
REM Before recording: close always-on-top widgets. The capture is a screen
REM region, so anything drawn over fman is burned into every frame.
setlocal

set "FMAN_NO_PAUSE=1"
call "%~dp0demos_record.bat" --demo 10 || exit /b 1

call "%~dp0demo_build_plugin_gifs.bat" || exit /b 1
pause
