@echo off
REM Print the full release label <version>_<build> (version from src/build/settings/base.json).
python "%~dp0release\build_number.py" label
