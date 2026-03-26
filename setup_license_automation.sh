#!/bin/bash

# Setup License Automation Services on VPS
# This script installs and starts deposit monitor and billing cron services

set -e

echo "======================================================================"
echo "SETUP LICENSE AUTOMATION SERVICES"
echo "======================================================================"
echo ""

# Check if running on VPS
if [ ! -d "/root/cryptomentor-bot/license_server" ]; then
    echo "ERROR: This script must be run on VPS"
    echo "Directory /root/cryptomentor-bot/license_server not found"
    exit 1
fi

cd /root/cryptomentor-bot/license_server

# Step 1: Install dependencies if needed
echo "[1/6] Checking dependencies..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing/updating dependencies..."
venv/bin/pip install -q -r requirements.txt

echo "✅ Dependencies OK"
echo ""

# Step 2: Copy service files
echo "[2/6] Installing systemd service files..."
sudo cp systemd/license-deposit.service /etc/systemd/system/
sudo cp systemd/license-billing.service /etc/systemd/system/

echo "✅ Service files installed"
echo ""

# Step 3: Reload systemd
echo "[3/6] Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "✅ Systemd reloaded"
echo ""

# Step 4: Enable services
echo "[4/6] Enabling services..."
sudo systemctl enable license-deposit
sudo systemctl enable license-billing

echo "✅ Services enabled"
echo ""

# Step 5: Start services
echo "[5/6] Starting services..."
sudo systemctl start license-deposit
sudo systemctl start license-billing

echo "✅ Services started"
echo ""

# Step 6: Check status
echo "[6/6] Checking service status..."
echo ""
echo "--- License Deposit Monitor ---"
sudo systemctl status license-deposit --no-pager | head -15
echo ""
echo "--- License Billing Cron ---"
sudo systemctl status license-billing --no-pager | head -15

echo ""
echo "======================================================================"
echo "✅ LICENSE AUTOMATION SETUP COMPLETED"
echo "======================================================================"
echo ""
echo "Services installed:"
echo "  1. license-deposit  - Monitors BSC blockchain for USDT deposits"
echo "  2. license-billing  - Daily billing cron at 00:00 UTC"
echo ""
echo "Commands:"
echo "  Check status : sudo systemctl status license-deposit license-billing"
echo "  View logs    : sudo journalctl -u license-deposit -f"
echo "  View logs    : sudo journalctl -u license-billing -f"
echo "  Restart      : sudo systemctl restart license-deposit license-billing"
echo ""
echo "Full automation is now active!"
echo ""
