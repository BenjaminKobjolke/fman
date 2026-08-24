@echo off
REM Record fman's demo screenshots/GIFs with the automated-application-screenshots
REM tool. Runs the tool from its own repo against fman's config; output lands in
REM <tool-repo>\output\demos-fman\demos\overview\ (demo.gif, demo.mp4, stills).
REM
REM Prereq (once): pip install -r requirements/windows-debug.txt
REM Usage: tools\demos_record.bat            (records every demo)
REM        tools\demos_record.bat --demo 1   (override; pass any tool args)
setlocal
set "TOOL_DIR=D:\GIT\BenjaminKobjolke\automated-application-screenshots"
set "CONFIG=%~dp0create_media\fman.json"
if "%~1"=="" (set "DEMO_ARGS=--demo all") else (set "DEMO_ARGS=%*")
cd /d "%TOOL_DIR%" || (echo Tool repo not found: %TOOL_DIR% & exit /b 1)
uv run screenshot-tool --config "%CONFIG%" %DEMO_ARGS%
