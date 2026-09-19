@echo off
setlocal
title TSUN Local - GEN4/1097 TCP Port Test

echo.
echo TSUN Local - GEN4/1097 TCP Port Test
echo =====================================
echo Default logger IP: 192.168.1.176
echo.
echo Keep this file in the same folder as:
echo   tsun_1097_port_restart_behavior_jeff.py
echo.

set "SCRIPT=%~dp0tsun_1097_port_restart_behavior_jeff.py"
if not exist "%SCRIPT%" (
  echo ERROR: Python script not found.
  pause
  exit /b 1
)

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=192.168.1.176"

where py >nul 2>&1
if %errorlevel%==0 (
  py -3 "%SCRIPT%" "%TARGET%"
  set "RC=%errorlevel%"
  goto done
)

where python >nul 2>&1
if %errorlevel%==0 (
  python "%SCRIPT%" "%TARGET%"
  set "RC=%errorlevel%"
  goto done
)

echo ERROR: Python 3 was not found.
echo Install Python 3 and run this file again.
set "RC=1"

:done
echo.
echo Finished with exit code %RC%.
pause
exit /b %RC%
