d:
cd "d:\GIT\BenjaminKobjolke\GPT-json-translator"
call .\.venv\Scripts\python.exe json_translator.py "d:\GIT\BenjaminKobjolke\fman\release_notes" --translate-recursive="en.json"
@set "RESULT=%ERRORLEVEL%"
cd %~dp0
@exit /b %RESULT%
