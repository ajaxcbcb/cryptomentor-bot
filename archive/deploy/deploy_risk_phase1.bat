@echo off
REM Deploy Risk Per Trade Phase 1 to VPS (Windows)
REM This script uses pscp (PuTTY SCP) to upload files

setlocal enabledelayedexpansion

echo ==========================================
echo Risk Per Trade Phase 1 Deployment
echo ==========================================
echo.

REM VPS Configuration
set VPS_HOST=147.93.156.165
set VPS_USER=root
set VPS_PATH=/root/cryptomentor-bot
set VPS_PASSWORD=<REDACTED_PASSWORD>

REM Check if files exist
echo Checking files...
set FILES=Bismillah\app\supabase_repo.py Bismillah\app\position_sizing.py Bismillah\app\handlers_autotrade.py

for %%f in (%FILES%) do (
    if not exist "%%f" (
        echo [ERROR] File not found: %%f
        exit /b 1
    )
    echo [OK] Found: %%f
)

echo.
echo VPS: %VPS_USER%@%VPS_HOST%
echo Path: %VPS_PATH%
echo.

REM Confirm deployment
set /p CONFIRM="Deploy to VPS? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo [CANCELLED] Deployment cancelled
    exit /b 0
)

echo.
echo Uploading files...

REM Check if pscp is available
where pscp >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pscp not found. Please install PuTTY or use manual deployment.
    echo.
    echo Manual deployment steps:
    echo 1. Open WinSCP or FileZilla
    echo 2. Connect to %VPS_HOST% with user %VPS_USER%
    echo 3. Upload these files to %VPS_PATH%/Bismillah/app/:
    for %%f in (%FILES%) do echo    - %%f
    echo 4. SSH to VPS and run: systemctl restart cryptomentor.service
    pause
    exit /b 1
)

REM Create backup on VPS
echo Creating backup...
echo y | plink -pw %VPS_PASSWORD% %VPS_USER%@%VPS_HOST% "mkdir -p %VPS_PATH%/backups/risk_phase1_$(date +%%Y%%m%%d_%%H%%M%%S) && cd %VPS_PATH%/Bismillah/app && cp supabase_repo.py handlers_autotrade.py %VPS_PATH%/backups/risk_phase1_$(date +%%Y%%m%%d_%%H%%M%%S)/ 2>/dev/null || true"

REM Upload files
for %%f in (%FILES%) do (
    echo Uploading %%f...
    pscp -pw %VPS_PASSWORD% "%%f" %VPS_USER%@%VPS_HOST%:%VPS_PATH%/%%f
    if !ERRORLEVEL! equ 0 (
        echo [OK] Uploaded: %%f
    ) else (
        echo [ERROR] Failed to upload: %%f
        exit /b 1
    )
)

echo.
echo Restarting service...

REM Restart service
echo y | plink -pw %VPS_PASSWORD% %VPS_USER%@%VPS_HOST% "systemctl restart cryptomentor.service && sleep 3 && systemctl status cryptomentor.service --no-pager -l"

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Deployment successful!
    echo.
    echo Next steps:
    echo 1. Check logs: ssh %VPS_USER%@%VPS_HOST% 'journalctl -u cryptomentor.service -n 50'
    echo 2. Test in Telegram: /autotrade - Settings - Risk Management
    echo 3. Verify risk settings work correctly
    echo.
    echo Rollback if needed:
    echo    ssh %VPS_USER%@%VPS_HOST% 'cd %VPS_PATH%/backups && ls -lt'
) else (
    echo.
    echo [ERROR] Service restart failed!
    echo Check logs manually
)

pause
