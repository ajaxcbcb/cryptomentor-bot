@echo off
REM Risk Mode Auto Setup Fix Deployment (Windows)

echo ==========================================
echo Risk Mode Auto Setup Fix Deployment
echo ==========================================
echo.

set VPS_USER=root
set VPS_HOST=147.93.156.165
set VPS_PATH=/root/cryptomentor-bot

echo Deploying fixed files to VPS...
echo.

echo 1. Deploying handlers_risk_mode.py (enhanced callback_select_risk_pct)...
scp Bismillah/app/handlers_risk_mode.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/

echo 2. Deploying handlers_autotrade.py (added callback_start_engine_now)...
scp Bismillah/app/handlers_autotrade.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/

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
echo What was fixed:
echo - Risk-based mode now truly automatic
echo - Bot fetches balance from exchange
echo - Bot auto-sets leverage to 10x
echo - Bot auto-calculates margin
echo - No manual input needed
echo.
echo Test in Telegram:
echo 1. Run /autotrade
echo 2. Complete API key setup
echo 3. Choose 'Rekomendasi' mode
echo 4. Select risk %% (e.g., 2%%)
echo 5. Verify bot shows 'Start AutoTrade' button
echo 6. Click and verify engine starts
echo.
echo Monitor logs:
echo ssh %VPS_USER%@%VPS_HOST% "journalctl -u cryptomentor.service -f"
echo.

pause
