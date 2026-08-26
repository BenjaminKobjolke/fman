@echo off
REM Re-vendor the Material icon set into
REM src\main\resources\base\Icons\Material from the npm package. Its output
REM is committed on purpose: fman must not need the network to draw an icon.
REM Pass --version 5.38.1 to pin a release instead of taking the latest.
setlocal
python "%~dp0fetch_material_icons.py" %*
endlocal
