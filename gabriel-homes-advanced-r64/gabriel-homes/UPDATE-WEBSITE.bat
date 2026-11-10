@echo off
rem ---------------------------------------------------------------------------
rem Gabriel Homes - Website Updater (Windows)  [v5.1 - offline repair + network-drive safe]
rem
rem What it does:
rem   1. Finds your REAL site folder - even when this file is started
rem      from inside an extracted update zip on a network share
rem   2. Finds the newest gabriel-homes-update-*.zip - including the
rem      REAL Downloads folder even when your company redirects it to
rem      a network path like \\KT-DC2\FolderRedir$\bkibet\Downloads
rem   3. Copies the new code over your site. Your database, photos,
rem      videos and accounts are NEVER touched.
rem   4. Runs the database migration and a final health check.
rem
rem You can also DRAG things onto this file instead of double-clicking:
rem   - drag the update zip onto it, or
rem   - drag your gabriel-homes site folder onto it.
rem
rem IMPORTANT after every update - restart the website so the new
rem pages go live: close the black website window (or double-click
rem STOP-WEBSITE.bat), then double-click START-GABRIEL-HOMES.bat,
rem then refresh your browser.
rem ---------------------------------------------------------------------------
setlocal EnableExtensions EnableDelayedExpansion
title Gabriel Homes - Website Updater

echo.
echo ==============================================================
echo   GABRIEL HOMES - website updater
echo ==============================================================
echo.

set "SRCDIR=%~dp0"
if "%SRCDIR:~-1%"=="\" set "SRCDIR=%SRCDIR:~0,-1%"
if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"

rem -- Drag-and-drop support: dropping the UPDATE ZIP onto this file
rem -- passes it as %%1; dropping a FOLDER passes the folder as %%1.
set "ZIPFROMARG="
set "SITEFROMARG="
if not "%~1"=="" (
    if /i "%~x1"==".zip" (
        set "ZIPFROMARG=%~f1"
    ) else if exist "%~1\" (
        set "SITEFROMARG=%~f1"
    )
)

rem ---------------------------------------------------------------
rem STEP 1 - find the REAL site folder: the one that contains
rem BOTH manage.py and db.sqlite3. An extracted update zip looks
rem almost the same but has NO db.sqlite3 - that is how we tell
rem them apart. When this updater sits in the extracted update
rem folder instead of the site, we search the usual install spots.
rem ---------------------------------------------------------------
set "SITE="

if defined SITEFROMARG (
    if exist "!SITEFROMARG!\manage.py" if exist "!SITEFROMARG!\db.sqlite3" set "SITE=!SITEFROMARG!"
)

if not defined SITE if exist "%SRCDIR%\manage.py" if exist "%SRCDIR%\db.sqlite3" set "SITE=%SRCDIR%"

if not defined SITE (
    for %%C in (
        "%LOCALAPPDATA%\GabrielHomes"
        "%USERPROFILE%\gabriel-homes"
        "%USERPROFILE%\Desktop\gabriel-homes"
        "%USERPROFILE%\Documents\gabriel-homes"
        "%USERPROFILE%\Downloads\gabriel-homes"
        "C:\gabriel-homes"
    ) do (
        if not defined SITE if exist "%%~C\manage.py" if exist "%%~C\db.sqlite3" set "SITE=%%~C"
    )
)

if not defined SITE (
    echo   I could not find your gabriel-homes site folder
    echo   automatically. It is the folder that contains BOTH
    echo   manage.py and db.sqlite3.
    echo.
    echo   Drag that folder into this window, then press ENTER.
    echo   Or just press ENTER to quit.
    set "SITEANS="
    set /p "SITEANS=Site folder: "
    if defined SITEANS (
        set "SITE=!SITEANS!"
        call :trim SITE
    )
)

if not defined SITE goto :fail_site
if not exist "!SITE!\manage.py" goto :fail_site

rem ---------------------------------------------------------------
rem STEP 1b - if the site lives on a NETWORK drive (a mapped drive
rem like Z: or a \\UNC path), the copy that actually RUNS is on the
rem LOCAL disk: START-GABRIEL-HOMES.bat moves it there because
rem databases stall on network drives. Update THAT local copy so
rem the updater and the launcher always agree.
rem ---------------------------------------------------------------
set "PROBEDRV=!SITE:~0,2!"
set "NETDRV="
if "!PROBEDRV!"=="\\" set "NETDRV=1"
if defined NETDRV goto :is_netdrive
fsutil fsinfo drivetype !PROBEDRV! 2>nul | findstr /i "Network" >nul
if not errorlevel 1 goto :is_netdrive
rem -- Locale-proof fallback: fsutil's "Network" word changes with the
rem -- Windows language, so when it found nothing, ask WMI for the
rem -- numeric drive type instead - 4 means network on every locale.
powershell -NoProfile -Command "if ((Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -eq '!PROBEDRV!' }).DriveType -eq 4) { exit 0 } else { exit 1 }" >nul 2>nul
if errorlevel 1 goto :site_local_done
:is_netdrive
if not exist "!LOCALAPPDATA!\GabrielHomes\manage.py" goto :site_local_done
if not exist "!LOCALAPPDATA!\GabrielHomes\db.sqlite3" goto :site_local_done
set "SITE=!LOCALAPPDATA!\GabrielHomes"
echo   Note: your website really runs from the local-disk copy at
echo     !SITE!
echo   because network drives stall the database - updating that copy.
echo.
:site_local_done

rem ---------------------------------------------------------------
rem STEP 2 - enter the site folder. pushd also works on NETWORK
rem paths \\server\..., where the plain 'cd' command fails and
rem silently drops us into C:\Windows - that was the old bug.
rem ---------------------------------------------------------------
pushd "!SITE!" || goto :fail_site
set "SITE=!CD!"

echo.
echo   Site folder : !SITE!
echo.

rem ---------------------------------------------------------------
rem STEP 3 - find the newest update zip.
rem The registry key below returns the REAL Downloads folder even
rem when the company has redirected it to a network share.
rem ---------------------------------------------------------------
set "ZIP="
if defined ZIPFROMARG set "ZIP=!ZIPFROMARG!"

if not defined ZIP (
    set "RDL="
    rem skip=1 jumps over the key header line so only the value line lands
    rem in RDL. The header contains a space and would corrupt the parse.
    for /f "skip=1 tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "{374DE290-123F-4565-9164-39C4925E467B}" 2^>nul') do set "RDL=%%b"
    if not defined RDL set "RDL=%USERPROFILE%\Downloads"

    for %%D in ("!RDL!" "%USERPROFILE%\Downloads" "%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%SRCDIR%" "!SITE!") do (
        if not defined ZIP for /f "delims=" %%z in ('dir /b /o-d "%%~D\gabriel-homes-update-*.zip" 2^>nul') do if not defined ZIP set "ZIP=%%~D\%%z"
    )
)

if not defined ZIP (
    echo   No gabriel-homes-update-*.zip was found in your Downloads,
    echo   Desktop, Documents or next to this file.
    echo.
    echo   Drag the update zip into this window and press ENTER.
    set "ZIPANS="
    set /p "ZIPANS=Update zip: "
    if defined ZIPANS (
        set "ZIP=!ZIPANS!"
        call :trim ZIP
    )
)

if not defined ZIP goto :fail_zip
if not exist "!ZIP!" goto :fail_zip

echo   Update file  : !ZIP!
echo.

rem ---------------------------------------------------------------
rem STEP 4 - look inside the zip: is it a valid update, and is the
rem code at the top level or wrapped in a gabriel-homes folder?
rem ---------------------------------------------------------------
set "ZIPLIST=%TEMP%\gabriel-zip-list.txt"
if exist "!ZIPLIST!" del "!ZIPLIST!" >nul 2>nul
tar -tf "!ZIP!" > "!ZIPLIST!" 2>nul
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::OpenRead('!ZIP!').Entries.FullName | Set-Content -LiteralPath '!ZIPLIST!'"
)
if not exist "!ZIPLIST!" goto :fail_notupdate
findstr /i /l /c:"manage.py" "!ZIPLIST!" >nul || goto :fail_notupdate

set "WRAPPED="
findstr /b /l /c:"gabriel-homes/" "!ZIPLIST!" >nul && set "WRAPPED=1"

rem ---------------------------------------------------------------
rem STEP 5 - copy the new code over the site. Only files carried
rem by the zip are overwritten - db.sqlite3 and media survive.
rem Written as goto-flow with NO parenthesized blocks on purpose:
rem CMD misparses ( ... ) blocks when a batch file has Unix line
rem endings, and paths containing ")" (e.g. "folder (1)") break
rem blocks at parse time. Goto-flow is immune to both.
rem ---------------------------------------------------------------
echo   Applying the update...
echo.

rem -- Always extract into a FRESH staging folder first, then
rem -- robocopy over the site. A failed or interrupted extraction
rem -- then never leaves a half-written site behind.
set "TMPX=%TEMP%\gabriel-update-x"
if exist "!TMPX!" rmdir /s /q "!TMPX!"
mkdir "!TMPX!"

rem -- tar.exe ships with Windows 10 1803+. When it is missing we
rem -- fall back to the .NET ZipFile extractor via PowerShell.
set "UNZIP="
where tar >nul 2>nul && set "UNZIP=tar"

set "XSRC=!TMPX!"
if defined WRAPPED set "XSRC=!TMPX!\gabriel-homes"

if defined WRAPPED goto :x_wrap
if defined UNZIP goto :x_tar_rootless
goto :x_ps_stage

:x_wrap
if defined UNZIP goto :x_tar_wrap
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::ExtractToDirectory('!ZIP!', '!TMPX!')"
if errorlevel 1 goto :fail_extract
goto :x_copy

:x_tar_rootless
tar -xf "!ZIP!" -C "!TMPX!"
if errorlevel 1 goto :fail_extract
goto :x_copy

:x_tar_wrap
tar -xf "!ZIP!" -C "!TMPX!"
if errorlevel 1 goto :fail_extract
goto :x_copy

:x_ps_stage
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::ExtractToDirectory('!ZIP!', '!TMPX!')"
if errorlevel 1 goto :fail_extract

:x_copy
robocopy "!XSRC!" "!CD!" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :fail_extract
rmdir /s /q "!TMPX!"

rem ---------------------------------------------------------------
rem STEP 6 - database migration + health check. Only runs when a
rem Python WITH Django is reachable: a freshly downloaded site
rem folder has no .venv yet (START-GABRIEL-HOMES.bat creates it and
rem runs this same migration on first start), so a Django-less
rem system Python must skip quietly - not dump import tracebacks.
rem ---------------------------------------------------------------
set "HOSTPY="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 set "HOSTPY=py -3"
if defined HOSTPY goto :env_ready
python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 set "HOSTPY=python"
if defined HOSTPY goto :env_ready
rem -- No Python on this machine at all. If a working .venv exists
rem -- we can still use it; otherwise skip the DB step gracefully -
rem -- START-GABRIEL-HOMES.bat installs Python and migrates on
rem -- first start.
if exist ".venv\Scripts\python.exe" goto :env_ready
goto :skip_db

:env_ready
if exist ".venv\Scripts\python.exe" goto :have_venv
echo   Creating the Python environment (one time, about a minute)...
!HOSTPY! -m venv .venv
if errorlevel 1 goto :fail_env
:have_venv
set "VPY=.venv\Scripts\python.exe"
"!VPY!" -c "import django" >nul 2>nul
if not errorlevel 1 goto :db_step

rem -- Django is missing or broken. OFFLINE repair from wheels first:
rem -- the zip bundles every Windows install wheel in wheels\.
if exist ".venv\.deps_ok" del ".venv\.deps_ok" >nul 2>nul
echo   Fixing the Python environment from the bundled wheels
echo   (works WITHOUT internet, about a minute)...
if not exist "wheels" goto :fix_online
"!VPY!" -m pip install --quiet --disable-pip-version-check --no-index --find-links wheels -r requirements.txt
if errorlevel 1 goto :fix_online
goto :fix_verify

:fix_online
echo   Bundled wheels unavailable - trying the internet...
"!VPY!" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :fix_rebuild
goto :fix_verify

:fix_rebuild
echo   Repair failed - rebuilding the environment from scratch...
if exist ".venv" rmdir /s /q ".venv"
if not defined HOSTPY goto :fail_env
!HOSTPY! -m venv .venv
if errorlevel 1 goto :fail_lock
if exist "wheels" goto :fix_rebuild_offline
"!VPY!" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :fail_db
goto :fix_verify

:fix_rebuild_offline
"!VPY!" -m pip install --quiet --disable-pip-version-check --no-index --find-links wheels -r requirements.txt
if errorlevel 1 goto :fail_db

:fix_verify
"!VPY!" -c "import django" >nul 2>nul
if errorlevel 1 goto :fail_db

:db_step
echo   Updating the database...
"!VPY!" manage.py migrate --noinput
if errorlevel 1 goto :fail_db
echo.
echo   Health check...
"!VPY!" manage.py check
if errorlevel 1 goto :fail_db
echo   Python environment, database and health check: all OK.
goto :done_banner

:skip_db
echo   NOTE: Python was not found on this machine, so the database
echo   step was skipped. That is normal for a fresh download and
echo   nothing is broken - START-GABRIEL-HOMES.bat installs Python
echo   and applies this database update automatically on first start.
goto :done_banner

:fail_env
echo.
echo   ERROR: no usable Python was found, so the database could not
echo   be updated. The website files WERE copied, but you must run
echo   START-GABRIEL-HOMES.bat once (it installs Python and finishes
echo   the update) before the site will work.
echo.
pause
exit /b 1

:fail_lock
echo.
echo   ERROR: could not rebuild the Python environment.
echo   Close other programs (especially the black website window)
echo   and run UPDATE-WEBSITE.bat again.
echo.
pause
exit /b 1

:fail_db
echo.
echo   ERROR: the database step failed - the website files were
echo   copied, but the update is NOT complete. Do NOT trust a
echo   half-updated site. Send the text of this window to the
echo   site administrator, then run UPDATE-WEBSITE.bat again.
echo.
pause
exit /b 1

:done_banner


echo.
echo ==============================================================
echo   DONE - update applied to:
echo     !SITE!
echo.
echo   Your listings, photos, videos and accounts were kept.
echo.
echo   NOW RESTART THE WEBSITE so the new pages go live:
echo     1. Close the black website window, or double-click
echo        STOP-WEBSITE.bat
echo     2. Double-click START-GABRIEL-HOMES.bat
echo     3. Refresh your browser
echo ==============================================================
echo.
popd
pause
exit /b 0

:fail_site
echo.
echo   ERROR: could not locate your site folder.
echo   Open the folder where the website lives - the one that
echo   contains BOTH manage.py and db.sqlite3 - and run this
echo   updater from there, or drag that folder onto this file.
echo.
pause
exit /b 1

:fail_zip
echo.
echo   ERROR: no update zip was given or found.
echo.
pause
exit /b 1

:fail_notupdate
echo.
echo   ERROR: this file does not look like a Gabriel Homes
echo   update zip - it must contain manage.py:
echo     !ZIP!
echo   Download gabriel-homes-update-*.zip and try again.
echo.
pause
exit /b 1

:fail_extract
echo.
echo   ERROR: could not extract the update zip.
echo   Close any program that may be using the site files -
echo   especially the black website window - and try again.
echo.
pause
exit /b 1

:trim
rem Removes trailing spaces and trailing backslashes from the variable
rem named by %%1. Paths dragged or pasted into a console window often
rem carry them, and pushd fails on them.
set "TRIMVAL=!%~1!"
:trim_loop
if not "!TRIMVAL!"=="" (
    if "!TRIMVAL:~-1!"==" " (
        set "TRIMVAL=!TRIMVAL:~0,-1!"
        goto :trim_loop
    )
    if "!TRIMVAL:~-1!"=="\" (
        set "TRIMVAL=!TRIMVAL:~0,-1!"
        goto :trim_loop
    )
)
set "%1=!TRIMVAL!"
set "TRIMVAL="
goto :eof
