@echo off
echo ============================================================
echo DEPLOYING MAINTENANCE NOTIFIER TO VPS
echo ============================================================
echo.

echo [1/4] Uploading maintenance_notifier.py...
pscp -pw <REDACTED_VPS_PASSWORD> Bismillah/app/maintenance_notifier.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
if errorlevel 1 (
    echo ERROR: Failed to upload maintenance_notifier.py
    pause
    exit /b 1
)
echo OK: maintenance_notifier.py uploaded
echo.

echo [2/4] Uploading scheduler.py...
pscp -pw <REDACTED_VPS_PASSWORD> Bismillah/app/scheduler.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
if errorlevel 1 (
    echo ERROR: Failed to upload scheduler.py
    pause
    exit /b 1
)
echo OK: scheduler.py uploaded
echo.

echo [3/4] Clearing Python cache...
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "cd /root/cryptomentor-bot && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -name '*.pyc' -delete"
echo OK: Cache cleared
echo.

echo [4/4] Restarting service...
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "systemctl restart cryptomentor.service"
echo OK: Service restarted
echo.

echo ============================================================
echo DEPLOYMENT COMPLETE!
echo ============================================================
echo.
echo The maintenance notifier will run automatically on next bot restart.
echo.
echo To verify deployment, check logs:
echo plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 -f"
echo.
echo Look for these log entries:
echo   [Maintenance] Checking for inactive engines...
echo   [Maintenance] Found X users with inactive engines
echo   [Maintenance] Notification Summary
echo.
pause
