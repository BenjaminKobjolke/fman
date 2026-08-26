@echo off
REM Sign a single exe via the XIDA network-share handshake (reuses release-tool PreSigner).
REM Usage: sign_exe.bat <path-to-exe>
REM ponytail: signing params hardcoded here, mirror publish_settings.ini [PreSigning]
REM           (the source of truth). Read from the ini only if the paths ever diverge.
REM PreSigner's default timeout of 300s is too short: the signing service has
REM returned fman.exe at ~5min01s, i.e. right at the boundary. 1800s instead.
setlocal
if "%~1"=="" (
    echo ERROR: no exe path given. Usage: sign_exe.bat ^<path-to-exe^>
    exit /b 1
)
if not exist "%~1" (
    echo ERROR: exe not found: %~1
    exit /b 1
)

cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -c "from release_tool.pre_signer import PreSigner,PreSignConfig; from pathlib import Path; PreSigner(PreSignConfig(True, r'//XIDA-SERVER/SigningExecutables/', r'//XIDA-SERVER/SigningExecutables/signed', 'XIDA GmbH', timeout=1800)).process(Path(r'%~1'))"
if errorlevel 1 (
    echo ERROR: signing failed for %~1
    exit /b 1
)
echo Signed: %~1
endlocal
exit /b 0
