@echo off
rem ---------------------------------------------------------------------------
rem Gabriel Homes - stop the local website (Windows)
rem Kills whatever is listening on ports 8000-8010 (the launcher's range).
rem ---------------------------------------------------------------------------
setlocal EnableExtensions
echo Stopping Gabriel Homes website...
set "FOUND=0"

for /l %%p in (8000,1,8010) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r /c:":%%p .*LISTENING"') do (
        taskkill /F /PID %%a >nul 2>nul
        if not errorlevel 1 (
            echo   Stopped process %%a on port %%p
            set "FOUND=1"
        )
    )
)

if "!FOUND!"=="0" echo   Nothing appears to be running.
if "!FOUND!"=="1" echo Done. The website is stopped.
pause
