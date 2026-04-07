@echo off
REM ============================================================
REM Deploy Demo User Update to VPS (Windows Batch)
REM ============================================================

echo ============================================================
echo 🚀 Deploying Demo User Update to VPS
echo ============================================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PowerShell not found! Please install PowerShell.
    pause
    exit /b 1
)

REM Run PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0deploy_demo_user_update.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo ✅ Deployment completed successfully!
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo ❌ Deployment failed! Check errors above.
    echo ============================================================
)

echo.
pause
