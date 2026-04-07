@echo off
REM Deploy StackMentor 60/30/10 Configuration Update
REM Updated: 2026-01-04

echo ========================================
echo StackMentor 60/30/10 Deployment
echo ========================================
echo.

echo [1/3] Uploading stackmentor.py to VPS...
pscp -pw <REDACTED_VPS_PASSWORD> Bismillah/app/stackmentor.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
if errorlevel 1 (
    echo ERROR: Upload failed!
    pause
    exit /b 1
)
echo OK - File uploaded
echo.

echo [2/3] Restarting cryptomentor service...
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "systemctl restart cryptomentor"
if errorlevel 1 (
    echo ERROR: Service restart failed!
    pause
    exit /b 1
)
echo OK - Service restarted
echo.

echo [3/3] Checking service status...
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "systemctl status cryptomentor --no-pager | head -20"
echo.

echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo StackMentor now configured as:
echo - TP1: 60%% @ R:R 1:2
echo - TP2: 30%% @ R:R 1:3
echo - TP3: 10%% @ R:R 1:5
echo.
echo Monitor logs with:
echo plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "journalctl -u cryptomentor -f --lines=50"
echo.
pause
