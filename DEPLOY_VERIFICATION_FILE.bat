@echo off
REM Batch script untuk upload Google verification file

echo ========================================
echo Upload Google Verification File
echo ========================================
echo.

REM Upload file
echo Uploading file...
pscp -pw "rMM2m63P" -P 22 "google25bce93832cdac80.html" root@147.93.156.165:/var/www/cryptomentor/google25bce93832cdac80.html

if %ERRORLEVEL% EQU 0 (
    echo.
    echo File uploaded successfully!
    echo.
    echo Setting permissions...
    plink -pw "rMM2m63P" -P 22 root@147.93.156.165 "chmod 644 /var/www/cryptomentor/google25bce93832cdac80.html && chown www-data:www-data /var/www/cryptomentor/google25bce93832cdac80.html"
    
    echo.
    echo Testing file...
    plink -pw "rMM2m63P" -P 22 root@147.93.156.165 "cat /var/www/cryptomentor/google25bce93832cdac80.html"
    
    echo.
    echo ========================================
    echo SUCCESS!
    echo ========================================
    echo.
    echo Test URL: https://cryptomentor.id/google25bce93832cdac80.html
    echo.
    echo Next: Go to Google Search Console and click VERIFIKASI
    echo.
) else (
    echo.
    echo Upload failed!
    echo Please check:
    echo 1. VPN is connected
    echo 2. Network connection is stable
    echo 3. VPS is accessible
    echo.
)

pause
