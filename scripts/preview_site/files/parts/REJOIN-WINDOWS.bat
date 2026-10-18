@echo off
setlocal
title Gabriel Homes - package rejoin
echo ============================================
echo  Gabriel Homes - rejoin the downloaded parts
echo ============================================
echo.
set ZIP=gabriel-homes-oneclick.zip
if exist "%ZIP%" (
  echo A %ZIP% already exists here. Delete it first if you want to rebuild it.
  pause
  exit /b 1
)
echo Step 1/2: joining the parts back into one zip...
copy /b /y "gabriel-homes-oneclick.part-*.bin" "%ZIP%" >nul
if errorlevel 1 (
  echo.
  echo FAILED: could not join the parts. Make sure ALL part files
  echo AND this .bat are in the same folder, then run it again.
  pause
  exit /b 1
)
echo           done.
echo.
echo Step 2/2: extracting the website...
tar -xf "%ZIP%"
if errorlevel 1 (
  echo tar.exe extract failed - right-click %ZIP% and choose
  echo "Extract All", then open the gabriel-homes folder.
  pause
  exit /b 1
)
echo.
echo ============================================================
echo  DONE. Your website is in the "gabriel-homes" folder.
echo  Next: open that folder and double-click
echo        START-GABRIEL-HOMES.bat
echo  The site opens in your browser automatically.
echo ============================================================
pause
