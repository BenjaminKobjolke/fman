@echo off
REM Run the theme engine's tests (fman_unittest.impl.test_themes /
REM test_theme). Excluded from `python build.py test` on purpose: that also
REM runs fman_integrationtest, which has a known intermittent hang - see
REM CLAUDE.md. Fast feedback when touching colors, styles.qss or Theme.css.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\unittest\python
python -m unittest -v ^
	fman_unittest.impl.test_themes fman_unittest.impl.test_theme
endlocal
