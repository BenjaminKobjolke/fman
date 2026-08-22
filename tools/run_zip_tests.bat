@echo off
REM Run the zip/7-Zip filesystem tests, excluded from `python build.py test`
REM because they spawn 7za.exe via a real console (winpty) and can hang
REM under AV/EDR interference or resource contention.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src\main\python
python -m unittest discover -v -p "zip_test.py" ^
	-s "%ROOT%\src\main\resources\base\Plugins\Core\core\tests\fs" ^
	-t "%ROOT%\src\main\resources\base\Plugins\Core"
endlocal
