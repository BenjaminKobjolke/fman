@echo off
REM Drive the automated-application-screenshots tool against fman's config.
REM Runs the tool from its own repo; output lands in fman's own media\demosREM (see output_dir in tools\create_mediaman.json).
REM
REM Every argument passes straight through to the tool, so this one file covers
REM recording, composing and inspecting.
REM
REM Prereq (once): pip install -r requirements/windows-debug.txt
REM   and, for the tour only, npm install in <tool-repo>\composer
REM
REM Usage: tools\demos_record.bat                        (records every demo)
REM        tools\demos_record.bat --demo 3               (one demo)
REM        tools\demos_record.bat --compose              (build all four artifacts)
REM        tools\demos_record.bat --compose features     (build one)
REM        tools\demos_record.bat --demo all --compose   (record, then build)
REM        tools\demos_record.bat --list                 (what this config can do)
setlocal
set "TOOL_DIR=D:\GIT\BenjaminKobjolke\automated-application-screenshots"
set "CONFIG=%~dp0create_media\fman.json"
if "%~1"=="" (set "DEMO_ARGS=--demo all") else (set "DEMO_ARGS=%*")
cd /d "%TOOL_DIR%" || (echo Tool repo not found: %TOOL_DIR% & exit /b 1)
uv run screenshot-tool --config "%CONFIG%" %DEMO_ARGS%
REM The pause is for double-clicking this file. Set FMAN_NO_PAUSE to run it
REM unattended (from another script, or a scheduled rebuild).
if not defined FMAN_NO_PAUSE pause