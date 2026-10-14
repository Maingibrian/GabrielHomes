#!/usr/bin/env python3
"""Upgrade v3 bats to v5.1 in one idempotent pass (CRLF line-splices only).

START-GABRIEL-HOMES.bat v3 -> v5.1:
  - network detection: UNC + fsutil + WMI DriveType fallback (locale-proof)
  - relocation to %LOCALAPPDATA%\GabrielHomes for ANY network drive (goto flow)
  - deps block: import-django gate -> offline wheels repair -> online ->
    full venv rebuild; :deps_giveup/:deps_lock honest failures

UPDATE-WEBSITE.bat v3 -> v5.1:
  - STEP 1b: probe found site's drive; if network + valid local copy exists,
    update THAT copy (launcher and updater agree on which copy is live)
  - STEP 6: HOSTPY detect -> create .venv -> import gate -> repair ladder
    (offline wheels -> online -> rebuild) -> migrate + check with errorlevel
    checks -> DONE banner only after real success; :fail_env/:fail_lock/
    :fail_db loud failures; graceful skip only when no Python exists at all.
"""
import sys
from pathlib import Path

MARKER = "v5.1"

PS = (
    'powershell -NoProfile -Command "if ((Get-CimInstance '
    'Win32_LogicalDisk | Where-Object {{ $_.DeviceID -eq \'{drv}\' }})'
    '.DriveType -eq 4) {{ exit 0 }} else {{ exit 1 }}" >nul 2>nul'
)

PIP_OFFLINE = (
    '"!VPY!" -m pip install --quiet --disable-pip-version-check '
    '--no-index --find-links wheels -r requirements.txt'
)
PIP_ONLINE = (
    '"!VPY!" -m pip install --quiet --disable-pip-version-check '
    '-r requirements.txt'
)


def read_lines(path: Path) -> list[str]:
    data = path.read_bytes()
    text = data.replace(b"\r\n", b"\n").decode("cp1252")
    return text.split("\n")


def write_crlf(path: Path, lines: list[str]) -> None:
    path.write_bytes("\r\n".join(lines).encode("cp1252"))


def find_idx(lines, prefix, what):
    for i, ln in enumerate(lines):
        if ln.startswith(prefix):
            return i
    raise SystemExit(f"FATAL: {what} not found")


# --------------------------------------------------------------------------
# START-GABRIEL-HOMES.bat
# --------------------------------------------------------------------------
def patch_start(p: Path) -> None:
    lines = read_lines(p)
    if any("[v5.1" in ln for ln in lines[:6]):
        print(f"  SKIP (already v5.1): {p.name}")
        return

    # -- header version tag
    i = find_idx(lines, "rem Gabriel Homes - one-click website launcher", "start header")
    lines[i] = "rem Gabriel Homes - one-click website launcher (Windows)  [v5.1]"
    i = find_idx(lines, "rem   2. Creates a .venv and installs dependencies", "deps line")
    lines[i] = ("rem   2. Creates a .venv and installs dependencies (bundled"
                " wheels work OFFLINE)")

    # -- replace RUNDIR set + v3 UNC-only parenthesized block with v5.1 flow
    a = find_idx(lines, 'set "RUNDIR=%SRCDIR%"', "RUNDIR set")
    b = find_idx(lines, "cd /d \"!RUNDIR!\"", "cd /d RUNDIR")
    block = [
        'set "RUNDIR=%SRCDIR%"',
        "",
        "rem -- Network location handling - UNC paths AND mapped drives.",
        "rem -- CMD cannot use a \\UNC path as a working directory at all, and a",
        "rem -- MAPPED network drive (Z:) is nearly as bad: Python and the SQLite",
        "rem -- database stall on the share and pages hang forever. So when the",
        "rem -- site sits on ANY network drive, it is copied to the LOCAL disk",
        "rem -- once, and afterwards always runs from that local copy.",
        'set "NETDRV="',
        'if "%SRCDIR:~0,2%"=="\\\\" set "NETDRV=1"',
        'fsutil fsinfo drivetype %SRCDIR:~0,2% 2>nul | findstr /i "Network" >nul && set "NETDRV=1"',
        "rem -- Locale-proof fallback: fsutil's \"Network\" word changes with the",
        "rem -- Windows language, so when it found nothing, ask WMI for the",
        "rem -- numeric drive type instead - 4 means network on every locale.",
        "if defined NETDRV goto :netdrv_done",
        PS.format(drv="%SRCDIR:~0,2%"),
        'if not errorlevel 1 set "NETDRV=1"',
        ":netdrv_done",
        "if not defined NETDRV goto :run_where_it_is",
        "",
        'if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\\AppData\\Local"',
        'set "LOCALDIR=!LOCALAPPDATA!\\GabrielHomes"',
        "echo   Your website is on a NETWORK drive. The database stalls on",
        "echo   network drives and pages hang forever, so the site runs from",
        "echo   your LOCAL disk instead:",
        "echo     !LOCALDIR!",
        'if exist "!LOCALDIR!\\manage.py" goto :use_local_copy',
        "echo   First run: copying the website over - one time, up to a minute...",
        'if not exist "!LOCALDIR!" mkdir "!LOCALDIR!"',
        'robocopy "%SRCDIR:~0,-1%" "!LOCALDIR!" /E /XF db.sqlite3 /XD .venv __pycache__ /NFL /NDL /NJH /NJS >nul',
        "if errorlevel 8 goto :fail_relocate",
        'if not exist "!LOCALDIR!\\db.sqlite3" copy /Y "%SRCDIR%db.sqlite3" "!LOCALDIR!\\db.sqlite3" >nul',
        "echo   Copied. The website and YOUR data - listings and enquiries -",
        "echo   now live in the local copy shown above.",
        ":use_local_copy",
        'set "RUNDIR=!LOCALDIR!\\"',
        "goto :rundir_ready",
        "",
        ":fail_relocate",
        "echo   ERROR: could not copy the site to your local disk.",
        "echo   Workaround: copy the gabriel-homes folder manually to your",
        "echo   Desktop or C:\\ drive, then run START-GABRIEL-HOMES.bat there.",
        "echo.",
        "pause",
        "exit /b 1",
        "",
        ":run_where_it_is",
        'set "RUNDIR=%SRCDIR%"',
        "",
        ":rundir_ready",
        "",
    ]
    lines[a:b] = block

    # -- replace deps block (v3 if/else) with goto-flow repair ladder
    a = find_idx(lines, 'if not exist ".venv\\.deps_ok" (', "deps block")
    b = find_idx(lines, "echo   Preparing database...", "prepare db")
    deps = [
        "rem -- Django gate: .venv can EXIST but be broken (an install that",
        "rem -- was interrupted, or a venv copied from another machine).",
        'rem -- Trust a working "import django", never the folder alone.',
        '"!VPY!" -c "import django" >nul 2>nul',
        "if not errorlevel 1 goto :deps_done",
        "",
        "rem -- Broken or missing dependencies. Try OFFLINE first: the",
        "rem -- update zip bundles every Windows wheel in wheels\\, so no",
        "rem -- internet is needed on networks that block pypi.org.",
        'if exist ".venv\\.deps_ok" del ".venv\\.deps_ok" >nul 2>nul',
        "echo   Python packages need attention. Installing from the bundled",
        "echo   wheels folder - works WITHOUT internet, about a minute...",
        'if exist "wheels" goto :deps_offline',
        "echo   No wheels folder found next to the site. Trying the internet...",
        "goto :deps_online",
        "",
        ":deps_offline",
        PIP_OFFLINE,
        "if errorlevel 1 goto :deps_online",
        "goto :deps_verify",
        "",
        ":deps_online",
        PIP_ONLINE,
        "if errorlevel 1 goto :deps_rebuild",
        "goto :deps_verify",
        "",
        ":deps_rebuild",
        "echo   Repair failed. Rebuilding the Python environment from scratch...",
        'if exist ".venv" rmdir /s /q ".venv"',
        "!PYCMD! -m venv .venv",
        "if errorlevel 1 goto :deps_lock",
        'if exist "wheels" goto :deps_rebuild_offline',
        PIP_ONLINE,
        "if errorlevel 1 goto :deps_giveup",
        "goto :deps_verify",
        "",
        ":deps_rebuild_offline",
        PIP_OFFLINE,
        "if errorlevel 1 goto :deps_giveup",
        "goto :deps_verify",
        "",
        ":deps_verify",
        '"!VPY!" -c "import django" >nul 2>nul',
        "if errorlevel 1 goto :deps_giveup",
        'type nul > ".venv\\.deps_ok"',
        "echo   Dependencies: OK",
        "",
        ":deps_done",
        "",
    ]
    lines[a:b] = deps

    # -- honest failure labels at the very end
    lines += [
        "",
        ":deps_giveup",
        "echo.",
        "echo   ERROR: could not install the Python packages, even from the",
        "echo   bundled wheels. The website cannot start.",
        "echo   Send the text of this window to the site administrator.",
        "echo.",
        "pause",
        "exit /b 1",
        "",
        ":deps_lock",
        "echo.",
        "echo   ERROR: could not rebuild the Python environment.",
        "echo   Close other programs and run START-GABRIEL-HOMES.bat again.",
        "echo.",
        "pause",
        "exit /b 1",
    ]
    write_crlf(p, lines)
    print(f"  PATCHED: {p.name} -> v5.1 ({len(lines)} lines)")


# --------------------------------------------------------------------------
# UPDATE-WEBSITE.bat
# --------------------------------------------------------------------------
def patch_updater(p: Path) -> None:
    lines = read_lines(p)
    if any("[v5.1" in ln for ln in lines[:6]):
        print(f"  SKIP (already v5.1): {p.name}")
        return

    i = find_idx(lines, "rem Gabriel Homes - Website Updater", "updater header")
    lines[i] = "rem Gabriel Homes - Website Updater (Windows)  [v5.1 - offline repair + network-drive safe]"

    # -- STEP 1b: local-copy probe after site validation
    a = find_idx(lines, 'if not exist "!SITE!\\manage.py" goto :fail_site', "site validation")
    probe = [
        "",
        "rem ---------------------------------------------------------------",
        "rem STEP 1b - if the site lives on a NETWORK drive (a mapped drive",
        "rem like Z: or a \\\\UNC path), the copy that actually RUNS is on the",
        "rem LOCAL disk: START-GABRIEL-HOMES.bat moves it there because",
        "rem databases stall on network drives. Update THAT local copy so",
        "rem the updater and the launcher always agree.",
        "rem ---------------------------------------------------------------",
        'set "PROBEDRV=!SITE:~0,2!"',
        'set "NETDRV="',
        'if "!PROBEDRV!"=="\\\\" set "NETDRV=1"',
        "if defined NETDRV goto :is_netdrive",
        'fsutil fsinfo drivetype !PROBEDRV! 2>nul | findstr /i "Network" >nul',
        "if not errorlevel 1 goto :is_netdrive",
        "rem -- Locale-proof fallback: fsutil's \"Network\" word changes with the",
        "rem -- Windows language, so when it found nothing, ask WMI for the",
        "rem -- numeric drive type instead - 4 means network on every locale.",
        PS.format(drv="!PROBEDRV!"),
        "if errorlevel 1 goto :site_local_done",
        ":is_netdrive",
        'if not exist "!LOCALAPPDATA!\\GabrielHomes\\manage.py" goto :site_local_done',
        'if not exist "!LOCALAPPDATA!\\GabrielHomes\\db.sqlite3" goto :site_local_done',
        'set "SITE=!LOCALAPPDATA!\\GabrielHomes"',
        "echo   Note: your website really runs from the local-disk copy at",
        "echo     !SITE!",
        "echo   because network drives stall the database - updating that copy.",
        "echo.",
        ":site_local_done",
    ]
    lines[a + 1:a + 1] = probe

    # -- STEP 6: replace probe+skip block with offline self-repair ladder
    a = find_idx(lines, 'set "PY="', "STEP6 probe")
    b = find_idx(lines, "echo. \r".replace("\r", "")) if False else None
    # end of STEP 6 block = the line "echo   NOW RESTART THE WEBSITE..." minus the
    # banner: find the DONE banner start after STEP 6. The block ends right before
    # the "echo." that precedes "echo ====..." DONE banner.
    e = find_idx(lines, "echo   DONE - update applied to:", "done banner")
    # walk back to the blank line before the banner's "echo." separator
    k = e
    while lines[k - 1].startswith("echo ="):
        k -= 1
    k -= 1  # the "echo." line
    k -= 1  # the blank line
    step6 = [
        'set "HOSTPY="',
        'py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul',
        'if not errorlevel 1 set "HOSTPY=py -3"',
        "if defined HOSTPY goto :env_ready",
        'python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul',
        'if not errorlevel 1 set "HOSTPY=python"',
        "if defined HOSTPY goto :env_ready",
        "rem -- No Python on this machine at all. If a working .venv exists",
        "rem -- we can still use it; otherwise skip the DB step gracefully -",
        "rem -- START-GABRIEL-HOMES.bat installs Python and migrates on",
        "rem -- first start.",
        'if exist ".venv\\Scripts\\python.exe" goto :env_ready',
        "goto :skip_db",
        "",
        ":env_ready",
        'if exist ".venv\\Scripts\\python.exe" goto :have_venv',
        "echo   Creating the Python environment (one time, about a minute)...",
        "!HOSTPY! -m venv .venv",
        "if errorlevel 1 goto :fail_env",
        ":have_venv",
        'set "VPY=.venv\\Scripts\\python.exe"',
        '"!VPY!" -c "import django" >nul 2>nul',
        "if not errorlevel 1 goto :db_step",
        "",
        "rem -- Django is missing or broken. OFFLINE repair from wheels first:",
        "rem -- the zip bundles every Windows install wheel in wheels\\.",
        'if exist ".venv\\.deps_ok" del ".venv\\.deps_ok" >nul 2>nul',
        "echo   Fixing the Python environment from the bundled wheels",
        "echo   (works WITHOUT internet, about a minute)...",
        'if not exist "wheels" goto :fix_online',
        PIP_OFFLINE,
        "if errorlevel 1 goto :fix_online",
        "goto :fix_verify",
        "",
        ":fix_online",
        "echo   Bundled wheels unavailable - trying the internet...",
        PIP_ONLINE,
        "if errorlevel 1 goto :fix_rebuild",
        "goto :fix_verify",
        "",
        ":fix_rebuild",
        "echo   Repair failed - rebuilding the environment from scratch...",
        'if exist ".venv" rmdir /s /q ".venv"',
        "if not defined HOSTPY goto :fail_env",
        "!HOSTPY! -m venv .venv",
        "if errorlevel 1 goto :fail_lock",
        'if exist "wheels" goto :fix_rebuild_offline',
        PIP_ONLINE,
        "if errorlevel 1 goto :fail_db",
        "goto :fix_verify",
        "",
        ":fix_rebuild_offline",
        PIP_OFFLINE,
        "if errorlevel 1 goto :fail_db",
        "",
        ":fix_verify",
        '"!VPY!" -c "import django" >nul 2>nul',
        "if errorlevel 1 goto :fail_db",
        "",
        ":db_step",
        "echo   Updating the database...",
        '"!VPY!" manage.py migrate --noinput',
        "if errorlevel 1 goto :fail_db",
        "echo.",
        "echo   Health check...",
        '"!VPY!" manage.py check',
        "if errorlevel 1 goto :fail_db",
        "echo   Python environment, database and health check: all OK.",
        "goto :done_banner",
        "",
        ":skip_db",
        "echo   NOTE: Python was not found on this machine, so the database",
        "echo   step was skipped. That is normal for a fresh download and",
        "echo   nothing is broken - START-GABRIEL-HOMES.bat installs Python",
        "echo   and applies this database update automatically on first start.",
        "goto :done_banner",
        "",
        ":fail_env",
        "echo.",
        "echo   ERROR: no usable Python was found, so the database could not",
        "echo   be updated. The website files WERE copied, but you must run",
        "echo   START-GABRIEL-HOMES.bat once (it installs Python and finishes",
        "echo   the update) before the site will work.",
        "echo.",
        "pause",
        "exit /b 1",
        "",
        ":fail_lock",
        "echo.",
        "echo   ERROR: could not rebuild the Python environment.",
        "echo   Close other programs (especially the black website window)",
        "echo   and run UPDATE-WEBSITE.bat again.",
        "echo.",
        "pause",
        "exit /b 1",
        "",
        ":fail_db",
        "echo.",
        "echo   ERROR: the database step failed - the website files were",
        "echo   copied, but the update is NOT complete. Do NOT trust a",
        "echo   half-updated site. Send the text of this window to the",
        "echo   site administrator, then run UPDATE-WEBSITE.bat again.",
        "echo.",
        "pause",
        "exit /b 1",
        "",
        ":done_banner",
        "",
    ]
    # replace from the "set \"PY=\"" line up to (not including) the banner's
    # first "echo." line right before the ===== banner
    lines[a:k] = step6

    # -- rename banner target: the DONE banner's preceding "echo." is the
    # :done_banner entry point already emitted above.
    write_crlf(p, lines)
    print(f"  PATCHED: {p.name} -> v5.1 ({len(lines)} lines)")


def main() -> int:
    root = Path("/home/z/my-project")
    start_bat = root / "scripts/launcher/START-GABRIEL-HOMES.bat"
    updater_bat = root / "gabriel_homes/UPDATE-WEBSITE.bat"
    patch_start(start_bat)
    patch_updater(updater_bat)
    for pth in (start_bat, updater_bat):
        data = pth.read_bytes()
        assert data.count(b"\r\n") == data.count(b"\n"), f"{pth}: LF-only lines leaked"
        assert data.count(MARKER.encode()) >= 1, f"{pth}: marker missing"
        print(f"  VERIFIED: {pth.name} CRLF-only, {len(data)} bytes")
    print("V5.1 PATCH OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
