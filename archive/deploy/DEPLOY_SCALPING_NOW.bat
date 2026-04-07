@echo off
REM Scalping Mode Deployment - Windows Batch Script
REM VPS: root@147.93.156.165

echo ========================================
echo Deploying Scalping Mode to VPS
echo ========================================
echo.

set VPS_HOST=root@147.93.156.165
set VPS_PATH=/root/cryptomentor-bot

echo Step 1: Upload database migration...
scp db/add_trading_mode.sql %VPS_HOST%:%VPS_PATH%/db/
if errorlevel 1 goto error

echo.
echo Step 2: Upload new files...
scp Bismillah/app/trading_mode.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
scp Bismillah/app/trading_mode_manager.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
scp Bismillah/app/scalping_engine.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
if errorlevel 1 goto error

echo.
echo Step 3: Upload modified files...
scp Bismillah/app/autosignal_fast.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
scp Bismillah/app/handlers_autotrade.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
scp Bismillah/app/autotrade_engine.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
if errorlevel 1 goto error

echo.
echo ========================================
echo Files uploaded successfully!
echo ========================================
echo.
echo Next: SSH to VPS and run these commands:
echo.
echo ssh %VPS_HOST%
echo cd %VPS_PATH%
echo pg_dump cryptomentor ^> backup_scalping_$(date +%%Y%%m%%d).sql
echo psql cryptomentor ^< db/add_trading_mode.sql
echo systemctl restart cryptomentor.service
echo journalctl -u cryptomentor.service -f
echo.
goto end

:error
echo.
echo ========================================
echo ERROR: Deployment failed!
echo ========================================
pause
exit /b 1

:end
echo Press any key to continue...
pause
