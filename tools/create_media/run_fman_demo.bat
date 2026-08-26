@echo off
REM Launch fman in demo mode for the automated-application-screenshots tool.
REM `python build.py run` (fbs) does not forward CLI args, so we launch the
REM main module directly the way fbs run does: PYTHONPATH=src\main\python.
REM
REM The tool starts this via `uv run`, which puts ITS virtualenv first on PATH
REM (that venv has neither fbs_runtime nor PyQt5). Drop that venv so `python`
REM falls back to the base install fman actually runs on. Override with
REM FMAN_PYTHON if your fman interpreter isn't the one on PATH.
REM Args from the tool: %1=demo id  %2=port  %3=width  %4=height
setlocal enabledelayedexpansion
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="
if not defined FMAN_PYTHON set "FMAN_PYTHON=python"
cd /d "%~dp0..\.."
set "PYTHONPATH=%CD%\src\main\python"

REM Record against a throwaway fman profile, never the developer's own: their
REM third-party plugins prepend key bindings (so they'd beat Core's) and add
REM palette commands that change what a typed query resolves to. Dropping
REM Plugins/ each run also resets the persisted viewer zoom/volume, so a
REM re-recording matches the first one. Redirecting APPDATA would do it too,
REM but that is also where pip --user puts PyQt5 and fbs_runtime - hence
REM fman's own FMAN_DATA_DIRECTORY override.
set "FMAN_DATA_DIRECTORY=%TEMP%\fman-demo-profile"
if exist "%FMAN_DATA_DIRECTORY%\Plugins" rmdir /s /q "%FMAN_DATA_DIRECTORY%\Plugins"
if not exist "%FMAN_DATA_DIRECTORY%\Local\libmpv" mkdir "%FMAN_DATA_DIRECTORY%\Local\libmpv"
REM Without a cached libmpv the first video view downloads ~100 MB behind a
REM progress dialog - on camera. Reuse the real profile's copy instead.
if not exist "%FMAN_DATA_DIRECTORY%\Local\libmpv\libmpv-2.dll" (
	if exist "%APPDATA%\fman\Local\libmpv\libmpv-2.dll" (
		copy /y "%APPDATA%\fman\Local\libmpv\libmpv-2.dll" "%FMAN_DATA_DIRECTORY%\Local\libmpv\" >nul
	) else (
		echo WARNING: no cached libmpv-2.dll - a video demo would record its download.
	)
)

REM ...but DO record in the developer's theme: a demo showing Monokai when the
REM screenshots elsewhere show their actual theme looks like a different app.
REM The theme lives in plain Local\Settings.json (fman reads it before the
REM plugin system exists), so copying that one file brings the look across
REM without any plugin or key binding. The window_opacity in it is ignored:
REM demo mode pins DEMO_OPACITY so every chapter records at a known value.
if exist "%APPDATA%\fman\Local\Settings.json" (
	copy /y "%APPDATA%\fman\Local\Settings.json" "%FMAN_DATA_DIRECTORY%\Local\" >nul
)
REM A custom theme lives outside the bundled Themes dir, so mirror those too -
REM otherwise load_theme silently falls back to the default.
if exist "%APPDATA%\fman\Themes" (
	xcopy /e /i /q /y "%APPDATA%\fman\Themes" "%FMAN_DATA_DIRECTORY%\Themes\" >nul
)

REM Demo 1 reads the committed examples. The tour chapters (id 3+) create,
REM rename, move and pack files, so they get a fresh scratch copy of both
REM example folders on the left and an empty folder on the right.
set "LEFT=%CD%\examples\left_pane"
set "RIGHT=%CD%\examples\right_pane"
if %1 GEQ 3 (
	set "LEFT=%TEMP%\fman-demo-%1-left"
	set "RIGHT=%TEMP%\fman-demo-%1-right"
	if exist "!LEFT!" rmdir /s /q "!LEFT!"
	if exist "!RIGHT!" rmdir /s /q "!RIGHT!"
	mkdir "!LEFT!"
	mkdir "!RIGHT!"
	xcopy /q /y "%CD%\examples\left_pane\*" "!LEFT!\" >nul
	xcopy /q /y "%CD%\examples\right_pane\*" "!LEFT!\" >nul
)

REM Chapter 8 (Go to) jumps around a small folder tree, and seeds this run
REM with its OWN Visited Paths.json. Both matter: SuggestLocations falls back
REM to the home directory subdirs when it finds 2 or fewer visited paths, and
REM it queries the Windows Search index once a query is longer than two chars
REM - either would put the recordist private folders on camera.
if "%1"=="8" mkdir "%LEFT%\projects\alpha" 2>nul
if "%1"=="8" mkdir "%LEFT%\projects\beta" 2>nul
if "%1"=="8" mkdir "%LEFT%\reports" 2>nul
if "%1"=="8" set "SETTINGS_DIR=%FMAN_DATA_DIRECTORY%\Plugins\User\Settings"
if "%1"=="8" powershell -NoProfile -Command "$s=$env:SETTINGS_DIR; New-Item -ItemType Directory -Force -Path $s | Out-Null; $l=$env:LEFT; $p=Join-Path $l 'projects'; $h=[ordered]@{}; $h[$l]=5; $h[$p]=4; $h[(Join-Path $p 'alpha')]=3; $h[(Join-Path $p 'beta')]=2; $h[(Join-Path $l 'reports')]=1; [System.IO.File]::WriteAllText((Join-Path $s 'Visited Paths.json'), ($h | ConvertTo-Json))"

REM Chapter 9 (tail mode) needs a log that actually GROWS while the viewer is
REM open - a static file cannot show the view following the end. Append a line
REM every 1.5 s for 60 s in the background, then stop on its own.
if "%1"=="9" set "LOGFILE=%LEFT%\service.log"
if "%1"=="9" powershell -NoProfile -Command "1..12 | ForEach-Object { Add-Content -LiteralPath $env:LOGFILE -Value ('{0:HH:mm:ss}  service started, worker {1} ready' -f (Get-Date), $_) }"
if "%1"=="9" start "" /b powershell -NoProfile -Command "1..40 | ForEach-Object { Add-Content -LiteralPath $env:LOGFILE -Value ('{0:HH:mm:ss}  request {1} handled in {2} ms' -f (Get-Date), $_, (Get-Random -Minimum 4 -Maximum 90)); Start-Sleep -Milliseconds 1500 }"

REM Clear the desktop before fman exists. The recorder grabs screen pixels of
REM fman's window rect, so anything drawn over it lands in the recording - and
REM the tool spawns one console per demo. This runs inside that console, so it
REM minimizes it too; fman starts afterwards and stays visible.
powershell -NoProfile -Command "(New-Object -ComObject Shell.Application).MinimizeAll()"

"%FMAN_PYTHON%" src\main\python\fman\main.py ^
  --automation-demo %1 ^
  --automation-demo-port %2 ^
  --automation-demo-width %3 ^
  --automation-demo-height %4 ^
  "%LEFT%" "%RIGHT%"
