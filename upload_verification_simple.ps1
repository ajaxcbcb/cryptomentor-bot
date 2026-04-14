# Simple PowerShell script untuk upload Google verification file

Write-Host "Creating verification file..." -ForegroundColor Yellow

# Create file
"google-site-verification: google25bce93832cdac80.html" | Out-File -FilePath "google25bce93832cdac80.html" -Encoding UTF8 -NoNewline

Write-Host "File created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Uploading to VPS..." -ForegroundColor Yellow

# Upload via SCP
scp google25bce93832cdac80.html root@147.93.156.165:/var/www/cryptomentor/

if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Setting permissions..." -ForegroundColor Yellow
    
    # Set permissions
    ssh root@147.93.156.165 "chmod 644 /var/www/cryptomentor/google25bce93832cdac80.html && chown www-data:www-data /var/www/cryptomentor/google25bce93832cdac80.html"
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! File is ready" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test URL: https://cryptomentor.id/google25bce93832cdac80.html" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next: Go back to Google Search Console and click VERIFIKASI" -ForegroundColor Yellow
} else {
    Write-Host "Upload failed. Please check SSH connection." -ForegroundColor Red
}

# Cleanup
Remove-Item google25bce93832cdac80.html -ErrorAction SilentlyContinue
