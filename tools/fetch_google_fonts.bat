@echo off
REM Re-vendor fman's bundled font families into
REM src\main\resources\base\Plugins\Core\Fonts from Google Fonts. Their
REM output is committed on purpose: fman must not need the network to draw
REM text. Pass --family "Fira Code" to refresh a single family.
setlocal
python "%~dp0fetch_google_fonts.py" %*
endlocal
