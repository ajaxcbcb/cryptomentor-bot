@echo off
REM ============================================================
REM Deploy BingX Updates to VPS using PuTTY
REM ============================================================

setlocal enabledelayedexpansion

set VPS_HOST=147.93.156.165
set VPS_USER=root
set VPS_PORT=22
set VPS_PASSWORD=<REDACTED_PASSWORD>
set VPS_PATH=/root/CryptoMentor

echo ============================================================
echo 🚀 Deploying BingX Updates to VPS
echo ============================================================
echo.
echo VPS: %VPS_USER%@%VPS_HOST%:%VPS_PORT%
echo Path: %VPS_PATH%
echo.

REM Check if plink and pscp are available
where plink >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: plink not found!
    echo.
    echo Please install PuTTY from:
    echo https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    echo.
    pause
    exit /b 1
)

where pscp >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: pscp not found!
    echo.
    echo Please install PuTTY from:
    echo https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    echo.
    pause
    exit /b 1
)

echo ✅ PuTTY tools found
echo.

REM ============================================================
REM Step 1: Create Backup on VPS
REM ============================================================

echo 📋 Step 1: Creating backup on VPS...
echo.

echo y | plink -ssh -P %VPS_PORT% -pw %VPS_PASSWORD% %VPS_USER%@%VPS_HOST% "cd /root/CryptoMentor && BACKUP_DIR=\"backups/bingx_update_$(date +%%Y%%m%%d_%%H%%M%%S)\" && mkdir -p \"$BACKUP_DIR\" && echo \"Creating backup in $BACKUP_DIR...\" && cp Bismillah/app/exchange_registry.py \"$BACKUP_DIR/\" 2>/dev/null || true && cp Bismillah/app/handlers_autotrade.py \"$BACKUP_DIR/\" 2>/dev/null || true && cp Bismillah/app/bingx_autotrade_client.py \"$BACKUP_DIR/\" 2>/dev/null || true && cp Bismillah/app/autotrade_engine.py \"$BACKUP_DIR/\" 2>/dev/null || true && cp Bismillah/app/scheduler.py \"$BACKUP_DIR/\" 2>/dev/null || true && echo \"✅ Backup created: $BACKUP_DIR\""

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create backup
    pause
    exit /b 1
)

echo.
echo ✅ Backup created successfully
echo.

REM ============================================================
REM Step 2: Upload Files
REM ============================================================

echo 📤 Step 2: Uploading updated files...
echo.

echo   Uploading exchange_registry.py...
echo y | pscp -P %VPS_PORT% -pw %VPS_PASSWORD% Bismillah\app\exchange_registry.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/exchange_registry.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upload exchange_registry.py
    pause
    exit /b 1
)

echo   Uploading handlers_autotrade.py...
echo y | pscp -P %VPS_PORT% -pw %VPS_PASSWORD% Bismillah\app\handlers_autotrade.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/handlers_autotrade.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upload handlers_autotrade.py
    pause
    exit /b 1
)

echo   Uploading bingx_autotrade_client.py...
echo y | pscp -P %VPS_PORT% -pw %VPS_PASSWORD% Bismillah\app\bingx_autotrade_client.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/bingx_autotrade_client.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upload bingx_autotrade_client.py
    pause
    exit /b 1
)

echo   Uploading autotrade_engine.py...
echo y | pscp -P %VPS_PORT% -pw %VPS_PASSWORD% Bismillah\app\autotrade_engine.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/autotrade_engine.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upload autotrade_engine.py
    pause
    exit /b 1
)

echo   Uploading scheduler.py...
echo y | pscp -P %VPS_PORT% -pw %VPS_PASSWORD% Bismillah\app\scheduler.py %VPS_USER%@%VPS_HOST%:%VPS_PATH%/Bismillah/app/scheduler.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upload scheduler.py
    pause
    exit /b 1
)

echo.
echo ✅ All files uploaded successfully!
echo.

REM ============================================================
REM Step 3: Restart Bot Service
REM ============================================================

echo 🔄 Step 3: Restarting bot service...
echo.

echo y | plink -ssh -P %VPS_PORT% -pw %VPS_PASSWORD% %VPS_USER%@%VPS_HOST% "cd /root/CryptoMentor && echo 'Stopping bot service...' && systemctl stop cryptomentor-bot && sleep 2 && echo 'Starting bot service...' && systemctl start cryptomentor-bot && sleep 3 && if systemctl is-active --quiet cryptomentor-bot; then echo '✅ Bot service started successfully!' && systemctl status cryptomentor-bot --no-pager | head -20; else echo '❌ Bot service failed to start!' && journalctl -u cryptomentor-bot -n 50 --no-pager && exit 1; fi"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Bot service failed to start!
    echo Check the logs above for errors.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ Deployment Complete!
echo ============================================================
echo.
echo 📊 Next steps:
echo   1. Monitor logs in PuTTY
echo   2. Test BingX registration flow
echo   3. Test BingX autotrade
echo.
echo 🔍 To monitor logs:
echo   plink -ssh -P %VPS_PORT% -pw %VPS_PASSWORD% %VPS_USER%@%VPS_HOST% "journalctl -u cryptomentor-bot -f"
echo.
echo 🔙 Rollback if needed:
echo   See DEPLOY_COMMANDS.txt for rollback instructions
echo.

pause
