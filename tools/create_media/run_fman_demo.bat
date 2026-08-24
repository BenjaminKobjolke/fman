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
setlocal
if defined VIRTUAL_ENV call set "PATH=%%PATH:%VIRTUAL_ENV%\Scripts;=%%"
set "VIRTUAL_ENV="
if not defined FMAN_PYTHON set "FMAN_PYTHON=python"
cd /d "%~dp0..\.."
set "PYTHONPATH=%CD%\src\main\python"
REM Demo 2 (the "tour") copies files into its right pane, so give it a fresh
REM empty temp dir instead of the committed examples\right_pane.
set "RIGHT=%CD%\examples\right_pane"
if "%~1"=="2" set "RIGHT=%TEMP%\fman-demo-tour"
if "%~1"=="2" if exist "%RIGHT%" rmdir /s /q "%RIGHT%"
if "%~1"=="2" mkdir "%RIGHT%"
"%FMAN_PYTHON%" src\main\python\fman\main.py ^
  --automation-demo %1 ^
  --automation-demo-port %2 ^
  --automation-demo-width %3 ^
  --automation-demo-height %4 ^
  examples\left_pane "%RIGHT%"
