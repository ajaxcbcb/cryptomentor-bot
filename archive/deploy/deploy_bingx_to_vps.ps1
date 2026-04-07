# ============================================================
# Deploy BingX Updates to VPS (PowerShell)
# ============================================================

$VPS_HOST = "147.93.156.165"
$VPS_USER = "root"
$VPS_PORT = "22"
$VPS_PATH = "/root/CryptoMentor"
$VPS_PASSWORD = "<REDACTED_PASSWORD>"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 Deploying BingX Updates to VPS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "VPS: $VPS_USER@$VPS_HOST:$VPS_PORT"
Write-Host "Path: $VPS_PATH"
Write-Host ""

# Files yang akan di-upload
$FILES_TO_UPLOAD = @(
    "Bismillah/app/exchange_registry.py",
    "Bismillah/app/handlers_autotrade.py",
    "Bismillah/app/bingx_autotrade_client.py",
    "Bismillah/app/autotrade_engine.py",
    "Bismillah/app/scheduler.py"
)

Write-Host "📦 Files to upload:" -ForegroundColor Yellow
foreach ($file in $FILES_TO_UPLOAD) {
    Write-Host "  - $file"
}
Write-Host ""

# Check if plink and pscp are available
$plinkPath = "plink"
$pscpPath = "pscp"

try {
    $null = Get-Command $plinkPath -ErrorAction Stop
    $null = Get-Command $pscpPath -ErrorAction Stop
} catch {
    Write-Host "❌ Error: plink or pscp not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install PuTTY tools:" -ForegroundColor Yellow
    Write-Host "  Download from: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html"
    Write-Host "  Or use: winget install PuTTY.PuTTY"
    Write-Host ""
    Write-Host "Alternative: Use WSL and run deploy_bingx_to_vps.sh instead"
    exit 1
}

# Create backup on VPS
Write-Host "📋 Step 1: Creating backup on VPS..." -ForegroundColor Yellow

$backupScript = @"
cd /root/CryptoMentor
BACKUP_DIR="backups/bingx_update_`$(date +%Y%m%d_%H%M%S)"
mkdir -p "`$BACKUP_DIR"
echo "Creating backup in `$BACKUP_DIR..."
cp -r Bismillah/app/exchange_registry.py "`$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/handlers_autotrade.py "`$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/bingx_autotrade_client.py "`$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/autotrade_engine.py "`$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/scheduler.py "`$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup created: `$BACKUP_DIR"
"@

echo $backupScript | & $plinkPath -ssh -P $VPS_PORT -pw $VPS_PASSWORD "$VPS_USER@$VPS_HOST"

Write-Host ""

# Upload files
Write-Host "📤 Step 2: Uploading updated files..." -ForegroundColor Yellow

foreach ($file in $FILES_TO_UPLOAD) {
    Write-Host "  Uploading $file..." -ForegroundColor Gray
    $remotePath = "$VPS_USER@$VPS_HOST`:$VPS_PATH/$file"
    & $pscpPath -P $VPS_PORT -pw $VPS_PASSWORD $file $remotePath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to upload $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ All files uploaded successfully!" -ForegroundColor Green
Write-Host ""

# Restart bot service
Write-Host "🔄 Step 3: Restarting bot service..." -ForegroundColor Yellow

$restartScript = @"
cd /root/CryptoMentor

# Check if bot is running
if systemctl is-active --quiet cryptomentor-bot; then
    echo "Stopping bot service..."
    systemctl stop cryptomentor-bot
    sleep 2
fi

# Start bot service
echo "Starting bot service..."
systemctl start cryptomentor-bot
sleep 3

# Check status
if systemctl is-active --quiet cryptomentor-bot; then
    echo "✅ Bot service started successfully!"
    systemctl status cryptomentor-bot --no-pager | head -20
else
    echo "❌ Bot service failed to start!"
    echo "Checking logs..."
    journalctl -u cryptomentor-bot -n 50 --no-pager
    exit 1
fi
"@

echo $restartScript | & $plinkPath -ssh -P $VPS_PORT -pw $VPS_PASSWORD "$VPS_USER@$VPS_HOST"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Monitor logs: plink -ssh -P $VPS_PORT -pw $VPS_PASSWORD $VPS_USER@$VPS_HOST 'journalctl -u cryptomentor-bot -f'"
Write-Host "  2. Test BingX registration flow"
Write-Host "  3. Test BingX autotrade"
Write-Host ""
Write-Host "🔙 Rollback if needed:" -ForegroundColor Yellow
Write-Host "  plink -ssh -P $VPS_PORT -pw $VPS_PASSWORD $VPS_USER@$VPS_HOST"
Write-Host "  cd /root/CryptoMentor/backups"
Write-Host "  ls -la  # Find backup directory"
Write-Host "  # Copy files back from backup"
Write-Host ""
