@echo off
REM Run MessageBox's layout tests (width floor, text alignment).
REM Excluded from `python build.py test` - hence the *_test.py name, which its
REM discovery does not match - because they need a QApplication of their own
REM and leftover Qt state is what makes that suite hang. See CLAUDE.md.
REM Offscreen, so no window appears.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python;%ROOT%\src\unittest\python
set QT_QPA_PLATFORM=offscreen
python -m unittest -v fman_unittest.impl.messagebox_layout_test
endlocal
