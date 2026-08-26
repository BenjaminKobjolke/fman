@echo off
REM Turn the recorded feature clips into the README's committed GIFs.
REM Record them first: tools\demos_record.bat --demo 8 (9).
REM Needs ffmpeg on PATH.
REM
REM GIF rather than MP4 because these sit inside the README's feature index:
REM GitHub renders a player only for a bare user-attachments URL on its own
REM line, which cannot live next to a paragraph. A 64-colour palette keeps a
REM 20 s clip under half a megabyte even with an animated theme behind it.
setlocal
set "REPO=%~dp0.."
set "OUT=%REPO%\media\demos\features"
if not exist "%OUT%" mkdir "%OUT%"

call :gif feature-goto goto
call :gif feature-tail tail
echo Done. Wrote %OUT%\goto.gif and %OUT%\tail.gif
exit /b 0

:gif
set "SRC=%REPO%\media\demos\%~1\demo.mp4"
if not exist "%SRC%" (
	echo Missing %SRC% - record it first with: tools\demos_record.bat --demo 8
	exit /b 1
)
ffmpeg -v error -y -i "%SRC%" -vf "fps=5,scale=800:-1:flags=lanczos,palettegen=max_colors=64" -frames:v 1 "%TEMP%\fman-gif-%~2.png"
ffmpeg -v error -y -i "%SRC%" -i "%TEMP%\fman-gif-%~2.png" -lavfi "fps=5,scale=800:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5" "%OUT%\%~2.gif"
del /q "%TEMP%\fman-gif-%~2.png" 2>nul
exit /b 0
