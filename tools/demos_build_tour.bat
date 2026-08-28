@echo off
REM Join the already-recorded tour-* chapters into
REM media\demos\tour\feature-tour.mp4 (Remotion, via the recording tool).
REM
REM Recording is a SEPARATE step - this builds from whatever is already in
REM media\demos\tour-*\demo.mp4:
REM     tools\demos_record.bat --demo 3     (and 4, 5, 6, 7)
REM
REM Prereq (once): npm install in <tool-repo>\composer - see docs\DEMOS.md
call "%~dp0demos_record.bat" --compose tour
