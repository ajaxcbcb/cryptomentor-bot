@echo off
echo ========================================
echo OpenClaw Gateway Test Runner
echo ========================================
echo.
echo This script will:
echo 1. Check if gateway is running
echo 2. If not, guide you to start it
echo 3. Run tests when ready
echo.
pause

:CHECK_GATEWAY
echo.
echo Checking gateway status...
cd Bismillah
python quick_test_gateway.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Gateway is running! Running full tests...
    echo ========================================
    echo.
    python test_openclaw_gateway.py
    goto END
) else (
    echo.
    echo ========================================
    echo Gateway is NOT running
    echo ========================================
    echo.
    echo Please start gateway in another terminal:
    echo.
    echo   1. Open NEW terminal window
    echo   2. Double-click: start_openclaw_gateway.bat
    echo   3. Wait for "Gateway listening on port 18789"
    echo   4. Come back here and press any key
    echo.
    pause
    goto CHECK_GATEWAY
)

:END
echo.
echo ========================================
echo Test completed!
echo ========================================
pause
