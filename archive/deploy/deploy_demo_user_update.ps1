# ============================================================
# Deploy Demo User Update to VPS (PowerShell)
# ============================================================

$VPS_HOST = "147.93.156.165"
$VPS_USER = "root"
$VPS_PORT = "22"
$VPS_PATH = "/root/CryptoMentor"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 Deploying Demo User Update to VPS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "VPS: $VPS_USER@$VPS_HOST:$VPS_PORT"
Write-Host "Path: $VPS_PATH"
Write-Host ""

# Files yang akan di-upload
$FILES_TO_UPLOAD = @(
    "Bismillah/app/demo_users.py",
    "Bismillah/app/handlers_community.py"
)

Write-Host "📦 Files to upload:" -ForegroundColor Yellow
foreach ($file in $FILES_TO_UPLOAD) {
    Write-Host "  - $file"
}
Write-Host ""

Write-Host "📝 Changes:" -ForegroundColor Yellow
Write-Host "  ✅ Added new demo user: Telegram UID 1234500004 (Bitunix UID: 933383167)"
Write-Host "  ✅ Blocked demo users from accessing Community Partners feature"
Write-Host ""

# Backup di VPS
Write-Host "📋 Step 1: Creating backup on VPS..." -ForegroundColor Green
$backupScript = @"
cd /root/CryptoMentor
BACKUP_DIR="backups/demo_user_update_`$(date +%Y%m%d_%H%M%S)"
mkdir -p "`$BACKUP_DIR"
echo "Creating backup in `$BACKUP_DIR..."
cp -r Bismillah/app/demo_users.py "`$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/handlers_community.py "`$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup created: `$BACKUP_DIR"
"@

ssh -p $VPS_PORT "$VPS_USER@$VPS_HOST" $backupScript

Write-Host ""

# Upload files
Write-Host "📤 Step 2: Uploading updated files..." -ForegroundColor Green
foreach ($file in $FILES_TO_UPLOAD) {
    Write-Host "  Uploading $file..." -ForegroundColor Gray
    scp -P $VPS_PORT $file "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/$file"
}

Write-Host ""
Write-Host "✅ All files uploaded successfully!" -ForegroundColor Green
Write-Host ""

# Restart bot service
Write-Host "🔄 Step 3: Restarting bot service..." -ForegroundColor Green
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

ssh -p $VPS_PORT "$VPS_USER@$VPS_HOST" $restartScript

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Demo User Configuration:" -ForegroundColor Yellow
Write-Host "  • Telegram UID: 1234500004"
Write-Host "  • Bitunix UID: 933383167"
Write-Host "  • Balance Limit: `$50 USD"
Write-Host "  • Community Partners: ❌ BLOCKED"
Write-Host ""
Write-Host "🔍 Verify deployment:" -ForegroundColor Yellow
Write-Host "  1. Monitor logs: ssh -p $VPS_PORT ${VPS_USER}@${VPS_HOST} 'journalctl -u cryptomentor-bot -f'"
Write-Host "  2. Test with demo user (Telegram ID: 1234500004)"
Write-Host "  3. Verify Community Partners access is blocked"
Write-Host ""
Write-Host "🔙 Rollback if needed:" -ForegroundColor Yellow
Write-Host "  ssh -p $VPS_PORT ${VPS_USER}@${VPS_HOST}"
Write-Host "  cd /root/CryptoMentor/backups"
Write-Host "  ls -la  # Find backup directory"
Write-Host "  # Copy files back from backup"
Write-Host ""
