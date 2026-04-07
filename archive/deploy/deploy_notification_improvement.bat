@echo off
echo ========================================
echo Deploying Notification Improvement
echo ========================================
echo.

echo [1/4] Uploading improved maintenance_notifier.py...
pscp -pw "<REDACTED_VPS_PASSWORD>" Bismillah/app/maintenance_notifier.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

echo.
echo [2/4] Clearing Python cache...
plink -batch -pw "<REDACTED_VPS_PASSWORD>" root@147.93.156.165 "cd /root/cryptomentor-bot && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -name '*.pyc' -delete"

echo.
echo [3/4] Restarting service...
plink -batch -pw "<REDACTED_VPS_PASSWORD>" root@147.93.156.165 "systemctl restart cryptomentor.service"

echo.
echo [4/4] Checking service status...
timeout /t 3 >nul
plink -batch -pw "<REDACTED_VPS_PASSWORD>" root@147.93.156.165 "systemctl status cryptomentor.service --no-pager -l"

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo WHAT'S NEW:
echo - Added 1-hour follow-up reminder for inactive engines
echo - Users will get a second notification if engine still inactive
echo - Improved user engagement and awareness
echo.
pause
