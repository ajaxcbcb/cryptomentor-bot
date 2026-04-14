# PowerShell script untuk upload Google verification file ke VPS

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📤 Upload Google Verification File" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$FILENAME = "google25bce93832cdac80.html"
$CONTENT = "google-site-verification: google25bce93832cdac80.html"
$VPS_USER = "root"
$VPS_IP = "147.93.156.165"
$VPS_PATH = "/var/www/cryptomentor"

Write-Host ""
Write-Host "📝 Creating verification file locally..." -ForegroundColor Yellow
$CONTENT | Out-File -FilePath $FILENAME -Encoding UTF8 -NoNewline
Write-Host "✅ File created: $FILENAME" -ForegroundColor Green

Write-Host ""
Write-Host "📤 Uploading to VPS..." -ForegroundColor Yellow
scp $FILENAME "${VPS_USER}@${VPS_IP}:${VPS_PATH}/"

Write-Host "✅ File uploaded successfully!" -ForegroundColor Green

Write-Host ""
Write-Host "🔧 Setting permissions on VPS..." -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_IP}" "chmod 644 ${VPS_PATH}/${FILENAME} && chown www-data:www-data ${VPS_PATH}/${FILENAME}"

Write-Host ""
Write-Host "✅ Done! Testing URL..." -ForegroundColor Green
Write-Host ""

# Test URL
Start-Sleep -Seconds 2
$testUrl = "https://cryptomentor.id/$FILENAME"
try {
    $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing
    Write-Host "Response from $testUrl :" -ForegroundColor Cyan
    Write-Host $response.Content -ForegroundColor White
} catch {
    Write-Host "⚠️  Could not test URL automatically, please test manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Verification file ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Kembali ke Google Search Console" -ForegroundColor White
Write-Host "   2. Klik tombol 'VERIFIKASI'" -ForegroundColor White
Write-Host "   3. Selesai!" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Test URL: $testUrl" -ForegroundColor Cyan

# Cleanup local file
Remove-Item -Path $FILENAME -ErrorAction SilentlyContinue
