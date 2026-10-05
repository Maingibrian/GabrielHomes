@echo off
rem ---------------------------------------------------------------------------
rem Gabriel Homes - one-click website launcher (Windows)  [v3]
rem
rem What it does:
rem   1. Finds (or installs via winget) Python 3.10+
rem   2. Creates a .venv and installs dependencies (first run, needs internet)
rem   3. Migrates + seeds ~80 demo listings (skipped automatically if data exists)
rem   4. Ensures demo accounts (admin + agent) exist
rem   5. Picks a free port (8000-8010), waits until the site answers,
rem      THEN opens your browser, and keeps the site running here
rem
rem New in v3: if this script is started from a NETWORK path (UNC, e.g. a
rem   corporate redirected Downloads folder \\server\...), CMD cannot use it
rem   as a working directory - so the site is copied to your LOCAL disk
rem   (%LOCALAPPDATA%\GabrielHomes) and runs from there automatically.
rem
rem Stop: close this window, or run STOP-WEBSITE.bat
rem Set GABRIEL_NO_BROWSER=1 to skip auto-opening the browser.
rem ---------------------------------------------------------------------------
setlocal EnableExtensions EnableDelayedExpansion
title Gabriel Homes
set "SRCDIR=%~dp0"

echo.
echo --------------------------------------------------------------
echo   GABRIEL HOMES - local website launcher
echo --------------------------------------------------------------

rem -- Guard: running from inside a zip preview window extracts only
rem -- THIS file to a temp folder; the rest of the project is missing.
if not exist "%SRCDIR%manage.py" (
    echo   ERROR: manage.py not found next to this script.
    echo   You probably ran it from INSIDE the zip window.
    echo   Please EXTRACT the whole zip first: right-click the zip,
    echo   choose "Extract All...", open the gabriel-homes folder,
    echo   then double-click START-GABRIEL-HOMES.bat there.
    pause
    exit /b 1
)

set "RUNDIR=%SRCDIR%"

rem -- Network path (UNC) handling. CMD does not support UNC paths as a
rem -- current directory: "cd /d \\server\share\..." fails and CMD silently
rem -- falls back to C:\Windows, where nothing of ours exists. Corporate
rem -- machines often redirect Downloads to \\server\FolderRedir$\... .
rem -- Fix: copy the site to the LOCAL disk and run it from there.
if "%SRCDIR:~0,2%"=="\\" (
    if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"
    set "LOCALDIR=!LOCALAPPDATA!\GabrielHomes"
    echo   Your folder is on a NETWORK drive, which Windows does not
    echo   allow Python to run from. Copying the website to your LOCAL
    echo   disk at "!LOCALDIR!" - one time, a few seconds...
    if not exist "!LOCALDIR!" mkdir "!LOCALDIR!"
    robocopy "%SRCDIR:~0,-1%" "!LOCALDIR!" /E /XF db.sqlite3 /XD .venv __pycache__ /NFL /NDL /NJH /NJS >nul
    if errorlevel 8 (
        echo   ERROR: could not copy the site to your local disk.
        echo   Workaround: copy the gabriel-homes folder manually to your
        echo   Desktop or C:\ drive, then run START-GABRIEL-HOMES.bat there.
        pause
        exit /b 1
    )
    if not exist "!LOCALDIR!\db.sqlite3" (
        copy /Y "%SRCDIR%db.sqlite3" "!LOCALDIR!\db.sqlite3" >nul
    )
    echo   Copied. The website will run from your local disk and your
    echo   data - listings and enquiries - is saved in the copy at
    echo   "!LOCALDIR!".
    set "RUNDIR=!LOCALDIR!\"
)

cd /d "!RUNDIR!"
if not exist "manage.py" (
    echo   ERROR: could not enter the site folder "!RUNDIR!".
    pause
    exit /b 1
)

set "NOBROWSER=!GABRIEL_NO_BROWSER!"
set "PYCMD="

rem -- Try the py launcher, then python on PATH.
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"

if not defined PYCMD (
    python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYCMD=python"
)

if not defined PYCMD (
    echo   Python 3.10+ not found. Trying to install via winget...
    where winget >nul 2>nul
    if not errorlevel 1 (
        winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    ) else (
        echo   winget not available on this system.
    )

    rem -- A freshly installed Python is NOT on PATH in this running
    rem -- session, so probe the standard install locations directly.
    py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYCMD=py -3"
)

if not defined PYCMD (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%ProgramFiles%\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%ProgramFiles%\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%ProgramFiles%\Python310\python.exe"
    ) do (
        if not defined PYCMD if exist %%P (
            call "%%~P" -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
            if not errorlevel 1 set PYCMD=%%P
        )
    )
)

if not defined PYCMD (
    echo.
    echo   Could not find or install Python automatically.
    echo   Opening https://www.python.org/downloads/
    echo   Install Python 3.12 and TICK "Add python.exe to PATH",
    echo   then run this file again.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

for /f "delims=" %%v in ('!PYCMD! --version 2^>^&1') do echo   Python: %%v

if not exist ".venv\Scripts\python.exe" (
    echo   Creating the .venv virtual environment - one time only...
    !PYCMD! -m venv .venv
    if errorlevel 1 (
        echo   ERROR: could not create the virtual environment.
        pause
        exit /b 1
    )
)
set "VPY=.venv\Scripts\python.exe"

if not exist ".venv\.deps_ok" (
    echo   Installing dependencies - first run needs internet, 1-3 min...
    "!VPY!" -m pip install --quiet --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo   ERROR: pip install failed - check your internet connection.
        echo   If you ran this from inside the zip window, extract the
        echo   WHOLE zip first, then run it from the extracted folder.
        pause
        exit /b 1
    )
    type nul > ".venv\.deps_ok"
) else (
    echo   Dependencies: OK
)

echo   Preparing database...
"!VPY!" manage.py migrate --noinput >nul 2>nul
if errorlevel 1 (
    echo   ERROR: database migration failed.
    pause
    exit /b 1
)
"!VPY!" manage.py seed_demo
if errorlevel 1 (
    echo   ERROR: demo data seeding failed.
    pause
    exit /b 1
)

"!VPY!" manage.py shell < scripts\setup_accounts.py
if errorlevel 1 (
    echo   ERROR: account setup failed.
    pause
    exit /b 1
)

set "PORT="
for /f "delims=" %%p in ('call "!VPY!" scripts\find_free_port.py') do set "PORT=%%p"
if not defined PORT (
    echo   ERROR: could not determine a free port.
    pause
    exit /b 1
)
if "!PORT!"=="0" (
    echo   ERROR: ports 8000-8010 are all in use. Close some apps and retry.
    pause
    exit /b 1
)

echo.
echo --------------------------------------------------------------
echo   Gabriel Homes is starting at:  http://127.0.0.1:!PORT!/
echo   Website:   http://127.0.0.1:!PORT!/
echo   Admin:     http://127.0.0.1:!PORT!/admin/     (admin@gabrielhomes.co.ke / gabriel2026^)
echo   Agent:     http://127.0.0.1:!PORT!/dashboard/  (hello@gabrielhomes.co.ke / gabriel2026^)
echo   Stop:      close this window, or run STOP-WEBSITE.bat
echo   Your browser will open as soon as the site is ready.
echo --------------------------------------------------------------
echo.

rem -- v2 fix: do NOT open the browser before the server listens.
rem -- Background this small waiter: it polls until the site answers,
rem -- then opens the default browser. Closing this window stops both.
if not "!NOBROWSER!"=="1" (
    start "" /b "!VPY!" scripts\open_browser_when_ready.py !PORT!
)

"!VPY!" manage.py runserver 127.0.0.1:!PORT! --noreload

echo.
echo   The website has stopped.
pause
