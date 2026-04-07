@echo off
REM Deploy UX Improvements to VPS
REM Date: April 3, 2026

set VPS_HOST=root@147.93.156.165
set VPS_PATH=/root/cryptomentor-bot
set SERVICE_NAME=cryptomentor.service

echo.
echo ========================================
echo   Deploy UX Improvements to VPS
echo ========================================
echo.

echo Step 1/4: Uploading UI components library...
scp Bismillah/app/ui_components.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
if errorlevel 1 goto error

echo.
echo Step 2/4: Uploading updated handlers...
scp Bismillah/app/handlers_autotrade.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
if errorlevel 1 goto error
scp Bismillah/app/handlers_risk_mode.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
if errorlevel 1 goto error

echo.
echo Step 3/4: Restarting service...
ssh %VPS_HOST% "systemctl restart %SERVICE_NAME%"
if errorlevel 1 goto error

echo.
echo Step 4/4: Checking service status...
timeout /t 3 /nobreak >nul
ssh %VPS_HOST% "systemctl status %SERVICE_NAME% --no-pager | head -20"

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.
echo What was deployed:
echo   - New UI components library
echo   - Updated autotrade handlers
echo   - Updated risk mode handlers
echo   - Improved settings menu
echo   - Better loading states
echo   - Success messages
echo.
echo Test the changes:
echo   1. /autotrade - Check welcome message
echo   2. Select exchange - Check progress
echo   3. Choose risk mode - Check cards
echo   4. Complete setup - Check success
echo   5. Open settings - Check sections
echo.
goto end

:error
echo.
echo ========================================
echo   ERROR: Deployment failed!
echo ========================================
echo.
pause
exit /b 1

:end
pause
