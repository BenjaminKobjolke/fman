@echo off
REM Increment the build number in build_version.txt and print the new value.
python "%~dp0release\build_number.py" increment
