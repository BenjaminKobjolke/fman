@echo off
REM Turn the recorded plugin clips into the README's committed GIFs.
REM Record them first: tools\demos_record.bat --demo 10.
REM Needs ffmpeg on PATH; gifsicle is optional but halves the result.
REM
REM GIF rather than MP4 for the same reason as the feature clips: GitHub renders
REM a player only for a bare user-attachments URL on its own line, which cannot
REM sit inside a table cell. See docs/DEMOS_PLUGINS.md.
REM
REM The knobs below are deliberately tighter than demo_build_feature_gifs.bat,
REM and they were measured on this clip rather than guessed. Matrix rain is
REM close to the worst case for GIF: every pixel changes every frame, so
REM inter-frame delta compression buys nothing and each frame is stored whole.
REM At the feature clips' 800px/5fps/64 colours the same 34 s take came out at
REM 7.1 MB.
REM
REM What did NOT help, all measured: dropping 64 colours to 24 (7.1 -> 6.6 MB),
REM turning dithering off, and paletteuse diff_mode=rectangle with palettegen
REM stats_mode=diff (no change at all - those exploit static regions, and there
REM are none here). Only two levers move it: pixel count, and gifsicle --lossy.
REM
REM Hence 360px. The README renders this at 320, so encoding at 640 was paying
REM four times the pixels to throw them away. And unlike the feature clips,
REM which demonstrate reading and typing, this one demonstrates an *effect* -
REM nobody needs to read the file names to see the rain fill one pane and then
REM both. A clip that does need legible text wants a wider setting here.
setlocal
set "REPO=%~dp0.."
set "OUT=%REPO%\media\demos\plugins"
set "GIF_FPS=4"
set "GIF_WIDTH=360"
set "GIF_COLORS=32"
set "GIF_LOSSY=60"
if not exist "%OUT%" mkdir "%OUT%"

call :gif plugin-matrix-rain matrix-rain || exit /b 1
echo Done. Wrote %OUT%\matrix-rain.gif

REM Keep the plugin's own README in step: it shows the same clip, and its repo
REM is the installed copy under %APPDATA%. Committing and pushing it there is
REM left to you - this repo has no business writing history in another one.
if exist "%APPDATA%\fman\Plugins\User\MatrixRain" (
	mkdir "%APPDATA%\fman\Plugins\User\MatrixRain\media" 2>nul
	copy /y "%OUT%\matrix-rain.gif" "%APPDATA%\fman\Plugins\User\MatrixRain\media\" >nul
	echo Also copied into the MatrixRain checkout - commit and push it there yourself.
)
exit /b 0

:gif
set "SRC=%REPO%\media\demos\%~1\demo.mp4"
if not exist "%SRC%" (
	echo Missing %SRC% - record it first with: tools\demos_record.bat --demo 10
	exit /b 1
)
ffmpeg -v error -y -i "%SRC%" -vf "fps=%GIF_FPS%,scale=%GIF_WIDTH%:-1:flags=lanczos,palettegen=max_colors=%GIF_COLORS%" -frames:v 1 "%TEMP%\fman-gif-%~2.png" || exit /b 1
ffmpeg -v error -y -i "%SRC%" -i "%TEMP%\fman-gif-%~2.png" -lavfi "fps=%GIF_FPS%,scale=%GIF_WIDTH%:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=none" "%OUT%\%~2.gif" || exit /b 1
del /q "%TEMP%\fman-gif-%~2.png" 2>nul

REM gifsicle --lossy is the one thing that meaningfully shrinks animated noise:
REM it lets nearly-identical pixels share a palette entry, which is exactly the
REM redundancy a rain of glyphs has and that ffmpeg cannot exploit. Worth about
REM 40%% here. Optional - without it the GIF is simply larger.
where gifsicle >nul 2>nul || (
	echo NOTE: gifsicle not on PATH - %~2.gif is larger than it needs to be.
	exit /b 0
)
gifsicle -O3 --lossy=%GIF_LOSSY% "%OUT%\%~2.gif" -o "%OUT%\%~2.opt.gif" 2>nul
if exist "%OUT%\%~2.opt.gif" move /y "%OUT%\%~2.opt.gif" "%OUT%\%~2.gif" >nul
exit /b 0
