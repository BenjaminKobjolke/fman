@echo off
REM Print the current build number from build_version.txt.
python "%~dp0release\build_number.py" get
