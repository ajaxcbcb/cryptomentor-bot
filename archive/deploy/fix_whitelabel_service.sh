#!/bin/bash
# Script untuk memperbaiki systemd service file whitelabel bot

echo "=== Fixing Whitelabel Bot Service ==="
echo ""

# Step 1: Verify folder name
echo "Step 1: Verifying folder name..."
cd /root/cryptomentor-bot
ls -la | grep -i white

echo ""
echo "Step 2: Checking current service file..."
cat /etc/systemd/system/whitelabel1.service

echo ""
echo "Step 3: Creating corrected service file..."

# Create corrected service file
sudo tee /etc/systemd/system/whitelabel1.service > /dev/null <<EOF
[Unit]
Description=Whitelabel #1 Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot/whitelabel-1
ExecStart=/root/cryptomentor-bot/whitelabel-1/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Step 4: Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "Step 5: Restarting whitelabel1 service..."
sudo systemctl restart whitelabel1

echo ""
echo "Step 6: Checking service status..."
sudo systemctl status whitelabel1

echo ""
echo "=== Done! ==="
echo ""
echo "To view logs, run:"
echo "sudo journalctl -u whitelabel1 -f"
