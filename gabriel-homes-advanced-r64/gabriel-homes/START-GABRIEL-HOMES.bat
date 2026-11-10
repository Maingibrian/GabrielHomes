@echo off
rem ---------------------------------------------------------------------------
rem Gabriel Homes - one-click website launcher (Windows)  [v5.1]
rem
rem What it does:
rem   1. Finds (or installs via winget) Python 3.10+
rem   2. Creates a .venv and installs dependencies (bundled wheels work OFFLINE)
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

rem -- Network location handling - UNC paths AND mapped drives.
rem -- CMD cannot use a \UNC path as a working directory at all, and a
rem -- MAPPED network drive (Z:) is nearly as bad: Python and the SQLite
rem -- database stall on the share and pages hang forever. So when the
rem -- site sits on ANY network drive, it is copied to the LOCAL disk
rem -- once, and afterwards always runs from that local copy.
set "NETDRV="
if "%SRCDIR:~0,2%"=="\\" set "NETDRV=1"
fsutil fsinfo drivetype %SRCDIR:~0,2% 2>nul | findstr /i "Network" >nul && set "NETDRV=1"
rem -- Locale-proof fallback: fsutil's "Network" word changes with the
rem -- Windows language, so when it found nothing, ask WMI for the
rem -- numeric drive type instead - 4 means network on every locale.
if defined NETDRV goto :netdrv_done
powershell -NoProfile -Command "if ((Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -eq '%SRCDIR:~0,2%' }).DriveType -eq 4) { exit 0 } else { exit 1 }" >nul 2>nul
if not errorlevel 1 set "NETDRV=1"
:netdrv_done
if not defined NETDRV goto :run_where_it_is

if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"
set "LOCALDIR=!LOCALAPPDATA!\GabrielHomes"
echo   Your website is on a NETWORK drive. The database stalls on
echo   network drives and pages hang forever, so the site runs from
echo   your LOCAL disk instead:
echo     !LOCALDIR!
if exist "!LOCALDIR!\manage.py" goto :use_local_copy
echo   First run: copying the website over - one time, up to a minute...
if not exist "!LOCALDIR!" mkdir "!LOCALDIR!"
robocopy "%SRCDIR:~0,-1%" "!LOCALDIR!" /E /XF db.sqlite3 /XD .venv __pycache__ /NFL /NDL /NJH /NJS >nul
if errorlevel 8 goto :fail_relocate
if not exist "!LOCALDIR!\db.sqlite3" copy /Y "%SRCDIR%db.sqlite3" "!LOCALDIR!\db.sqlite3" >nul
echo   Copied. The website and YOUR data - listings and enquiries -
echo   now live in the local copy shown above.
:use_local_copy
set "RUNDIR=!LOCALDIR!\"
goto :rundir_ready

:fail_relocate
echo   ERROR: could not copy the site to your local disk.
echo   Workaround: copy the gabriel-homes folder manually to your
echo   Desktop or C:\ drive, then run START-GABRIEL-HOMES.bat there.
echo.
pause
exit /b 1

:run_where_it_is
set "RUNDIR=%SRCDIR%"

:rundir_ready

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

rem -- Django gate: .venv can EXIST but be broken (an install that
rem -- was interrupted, or a venv copied from another machine).
rem -- Trust a working "import django", never the folder alone.
"!VPY!" -c "import django" >nul 2>nul
if not errorlevel 1 goto :deps_done

rem -- Broken or missing dependencies. Try OFFLINE first: the
rem -- update zip bundles every Windows wheel in wheels\, so no
rem -- internet is needed on networks that block pypi.org.
if exist ".venv\.deps_ok" del ".venv\.deps_ok" >nul 2>nul
echo   Python packages need attention. Installing from the bundled
echo   wheels folder - works WITHOUT internet, about a minute...
if exist "wheels" goto :deps_offline
echo   No wheels folder found next to the site. Trying the internet...
goto :deps_online

:deps_offline
"!VPY!" -m pip install --quiet --disable-pip-version-check --no-index --find-links wheels -r requirements.txt
if errorlevel 1 goto :deps_online
goto :deps_verify

:deps_online
"!VPY!" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :deps_rebuild
goto :deps_verify

:deps_rebuild
echo   Repair failed. Rebuilding the Python environment from scratch...
if exist ".venv" rmdir /s /q ".venv"
!PYCMD! -m venv .venv
if errorlevel 1 goto :deps_lock
if exist "wheels" goto :deps_rebuild_offline
"!VPY!" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :deps_giveup
goto :deps_verify

:deps_rebuild_offline
"!VPY!" -m pip install --quiet --disable-pip-version-check --no-index --find-links wheels -r requirements.txt
if errorlevel 1 goto :deps_giveup
goto :deps_verify

:deps_verify
"!VPY!" -c "import django" >nul 2>nul
if errorlevel 1 goto :deps_giveup
type nul > ".venv\.deps_ok"
echo   Dependencies: OK

:deps_done

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


:deps_giveup
echo.
echo   ERROR: could not install the Python packages, even from the
echo   bundled wheels. The website cannot start.
echo   Send the text of this window to the site administrator.
echo.
pause
exit /b 1

:deps_lock
echo.
echo   ERROR: could not rebuild the Python environment.
echo   Close other programs and run START-GABRIEL-HOMES.bat again.
echo.
pause
exit /b 1