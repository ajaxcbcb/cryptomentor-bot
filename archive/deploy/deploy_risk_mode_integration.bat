@echo off
REM Risk Mode Integration Deployment Script (Windows)
REM Deploys risk mode selection to VPS

echo ==========================================
echo Risk Mode Integration Deployment
echo ==========================================
echo.

set VPS_USER=root
set VPS_HOST=147.93.156.165
set VPS_PATH=/root/cryptomentor-bot

echo Deploying files to VPS...
echo.

echo 1. Deploying handlers_autotrade.py...
scp Bismillah/app/handlers_autotrade.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/

echo 2. Deploying handlers_risk_mode.py...
scp Bismillah/app/handlers_risk_mode.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/

echo 3. Deploying supabase_repo.py...
scp Bismillah/app/supabase_repo.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/

echo.
echo Files deployed successfully!
echo.

echo Restarting service...
ssh %VPS_USER%@%VPS_HOST% "systemctl restart cryptomentor.service"

echo.
echo Waiting for service to start...
timeout /t 3 /nobreak >nul

echo.
echo Checking service status...
ssh %VPS_USER%@%VPS_HOST% "systemctl status cryptomentor.service --no-pager -l"

echo.
echo ==========================================
echo Deployment Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Run database migration: db/add_risk_mode.sql
echo 2. Test with /autotrade command in Telegram
echo 3. Monitor logs: ssh %VPS_USER%@%VPS_HOST% "journalctl -u cryptomentor.service -f"
echo.

pause
