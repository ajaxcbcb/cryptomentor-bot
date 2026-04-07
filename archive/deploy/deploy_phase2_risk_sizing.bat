@echo off
REM Deploy Phase 2: Risk-Based Position Sizing to VPS
REM Date: April 2, 2026
REM CRITICAL: This modifies core trading logic - deploy carefully!

set VPS_HOST=root@147.93.156.165
set VPS_PATH=/root/cryptomentor-bot
set SERVICE_NAME=cryptomentor.service

echo ============================================
echo Phase 2: Risk-Based Position Sizing Deploy
echo ============================================
echo.
echo WARNING: This modifies core trading logic!
echo WARNING: Make sure you have reviewed all changes!
echo.
set /p confirm="Continue? (yes/no): "

if not "%confirm%"=="yes" (
    echo Deployment cancelled.
    exit /b 1
)

echo.
echo Step 1: Creating backups on VPS...
ssh %VPS_HOST% "cd %VPS_PATH%/Bismillah/app && cp autotrade_engine.py autotrade_engine.py.phase2_backup_$(date +%%Y%%m%%d_%%H%%M%%S) && cp scalping_engine.py scalping_engine.py.phase2_backup_$(date +%%Y%%m%%d_%%H%%M%%S) && echo 'Backups created'"

echo.
echo Step 2: Uploading modified files...
scp Bismillah/app/autotrade_engine.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
scp Bismillah/app/scalping_engine.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
echo Files uploaded

echo.
echo Step 3: Verifying files...
ssh %VPS_HOST% "cd %VPS_PATH%/Bismillah/app && grep -q 'calc_qty_with_risk' autotrade_engine.py && echo 'autotrade_engine.py updated' || echo 'autotrade_engine.py NOT updated'"
ssh %VPS_HOST% "cd %VPS_PATH%/Bismillah/app && grep -q 'used_risk_sizing' scalping_engine.py && echo 'scalping_engine.py updated' || echo 'scalping_engine.py NOT updated'"

echo.
echo Step 4: Restarting service...
ssh %VPS_HOST% "systemctl restart %SERVICE_NAME%"
echo Service restarted

echo.
echo Step 5: Checking service status...
timeout /t 3 /nobreak >nul
ssh %VPS_HOST% "systemctl status %SERVICE_NAME% --no-pager | head -20"

echo.
echo Step 6: Checking logs for errors...
ssh %VPS_HOST% "journalctl -u %SERVICE_NAME% -n 50 --no-pager | grep -i 'error\|exception\|failed' || echo 'No errors in recent logs'"

echo.
echo ============================================
echo Phase 2 Deployment Complete!
echo ============================================
echo.
echo CRITICAL: Monitor closely for next 24-48 hours!
echo.
echo What was deployed:
echo    - Risk-based position sizing in autotrade_engine.py
echo    - Risk-based position sizing in scalping_engine.py
echo    - Fallback to fixed margin if risk calculation fails
echo.
echo Monitoring commands:
echo    ssh %VPS_HOST% "journalctl -u %SERVICE_NAME% -f"
echo    ssh %VPS_HOST% "journalctl -u %SERVICE_NAME% -n 100 | grep RiskSizing"
echo.
echo Rollback if needed:
echo    ssh %VPS_HOST% "cd %VPS_PATH%/Bismillah/app && cp autotrade_engine.py.phase2_backup_* autotrade_engine.py && systemctl restart %SERVICE_NAME%"
echo.
pause
