@echo off
REM Deploy Risk Calculator to VPS (Windows)

set VPS_HOST=root@147.93.156.165
set VPS_PATH=/root/cryptomentor-bot
set PASSWORD=<REDACTED_PASSWORD>

echo ==========================================
echo   Deploy Risk Calculator Module
echo ==========================================
echo.

REM Step 1: Deploy risk_calculator.py
echo Step 1: Deploying risk_calculator.py...
scp Bismillah/app/risk_calculator.py %VPS_HOST%:%VPS_PATH%/Bismillah/app/
if errorlevel 1 (
    echo ERROR: Failed to deploy risk_calculator.py
    pause
    exit /b 1
)
echo OK: risk_calculator.py deployed
echo.

REM Step 2: Test module on VPS
echo Step 2: Testing module on VPS...
ssh %VPS_HOST% "cd /root/cryptomentor-bot && python3 -c \"from Bismillah.app.risk_calculator import calculate_position_size; r=calculate_position_size(1000,2,66500,65500); print(r); assert r['status']=='success'\""
if errorlevel 1 (
    echo ERROR: Module test failed
    pause
    exit /b 1
)
echo OK: Module tested successfully
echo.

REM Step 3: Backup current autotrade_engine.py
echo Step 3: Backing up autotrade_engine.py...
ssh %VPS_HOST% "cd /root/cryptomentor-bot/Bismillah/app && cp autotrade_engine.py autotrade_engine.py.backup_$(date +%%Y%%m%%d_%%H%%M%%S)"
echo OK: Backup created
echo.

echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Update autotrade_engine.py to use new risk_calculator
echo 2. Restart service: systemctl restart cryptomentor.service
echo 3. Monitor logs: journalctl -u cryptomentor.service -f
echo.
echo Module deployed to: %VPS_PATH%/Bismillah/app/risk_calculator.py
echo.
pause
