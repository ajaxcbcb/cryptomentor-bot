# Deploy CryptoMentor Frontend ke VPS
# Fitur:
# - Build frontend otomatis
# - Deploy semua file dari dist/
# - Reload nginx service
# - Verify deployment
#
# Requirement: curl atau OpenSSH for Windows

param(
    [string]$Host = "147.93.156.165",
    [string]$User = "root",
    [string]$Password = $env:VPS_PASSWORD,
    [string]$DestDir = "/var/www/cryptomentor",
    [switch]$SkipBuild
)

$FrontendDir = "website-frontend"
$DistDir = "$FrontendDir/dist"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 DEPLOY FRONTEND CRYPTOMENTOR" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Frontend
if (-not $SkipBuild) {
    Write-Host "📦 Building frontend..." -ForegroundColor Yellow
    
    # Check if npm exists
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Host "✗ npm tidak ditemukan!" -ForegroundColor Red
        Write-Host "  Install Node.js dari: https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }
    
    # Install dependencies if needed
    if (-not (Test-Path "$FrontendDir/node_modules")) {
        Write-Host "  Installing dependencies..."
        Push-Location $FrontendDir
        npm install
        Pop-Location
    }
    
    # Build
    Push-Location $FrontendDir
    npm run build
    $BuildSuccess = $LASTEXITCODE -eq 0
    Pop-Location
    
    if (-not $BuildSuccess) {
        Write-Host "✗ Build gagal!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Build berhasil!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⏭ Skipping build..." -ForegroundColor Yellow
}

# Step 2: Check dist files
if (-not (Test-Path $DistDir)) {
    Write-Host "✗ Directory $DistDir tidak ditemukan!" -ForegroundColor Red
    exit 1
}

$FileCount = @(Get-ChildItem -Path $DistDir -Recurse -File).Count
Write-Host "📊 Siap deploy $FileCount files" -ForegroundColor Green
Write-Host ""

# Step 3: Get authentication
Write-Host "🔐 Autentikasi ke VPS..." -ForegroundColor Yellow

if (-not $Password) {
    $Password = Read-Host -AsSecureString "  Masukkan VPS password (SSH)"
    $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($Password))
}

# Step 4: Deploy dengan SCP
Write-Host "📁 Uploading files..." -ForegroundColor Yellow

$ScpCommand = 'scp -r -P 22'

# Check if OpenSSH is available
if (Get-Command scp -ErrorAction SilentlyContinue) {
    Write-Host "  Using OpenSSH SCP" -ForegroundColor Green
    
    # Deploy dist folder
    $ScpCmd = "scp -r -P 22 `"$DistDir/*`" `"$User@$Host`:$DestDir/`""
    Invoke-Expression $ScpCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Upload gagal!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Files uploaded!" -ForegroundColor Green
    
    # Reload nginx
    Write-Host ""
    Write-Host "🔄 Reloading nginx..." -ForegroundColor Yellow
    $NginxCmd = "ssh -p 22 $User@$Host 'sudo systemctl reload nginx'"
    Invoke-Expression $NginxCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Nginx reloaded!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Nginx reload failed" -ForegroundColor Yellow
    }
    
    # Verify
    Write-Host ""
    Write-Host "✅ Verifying deployment..." -ForegroundColor Yellow
    $VerifyCmd = "ssh -p 22 $User@$Host 'ls -la $DestDir/'"
    Invoke-Expression $VerifyCmd | Select-Object -First 10
    
} else {
    Write-Host "⚠ OpenSSH SCP not available" -ForegroundColor Red
    Write-Host "  Install: Windows 10+ (openssh-client) or use Python script" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ DEPLOY SELESAI!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   Frontend: https://cryptomentor.id" -ForegroundColor Cyan
Write-Host "   API: https://cryptomentor.id/api" -ForegroundColor Cyan
Write-Host ""
