#!/bin/bash
# Setup script untuk Whitelabel #1 di VPS (run di VPS)
# Usage: bash setup_whitelabel_vps.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Whitelabel #1 Bot - VPS Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

BOT_DIR="/root/cryptomentor-bot/Whitelabel #1"

# Check if directory exists
if [ ! -d "$BOT_DIR" ]; then
    echo -e "${RED}Error: Directory not found: $BOT_DIR${NC}"
    exit 1
fi

cd "$BOT_DIR"

echo -e "${BLUE}1. Installing dependencies...${NC}"
pip3 install -r requirements.txt

echo ""
echo -e "${BLUE}2. Creating systemd service...${NC}"

cat > /etc/systemd/system/whitelabel1.service << 'EOF'
[Unit]
Description=Whitelabel #1 CryptoMentor Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot/Whitelabel #1
ExecStart=/usr/bin/python3 /root/cryptomentor-bot/Whitelabel #1/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Service file created${NC}"

echo ""
echo -e "${BLUE}3. Configuring environment...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  IMPORTANT: Edit .env file with your credentials!${NC}"
    echo -e "${YELLOW}Run: nano '$BOT_DIR/.env'${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create data directory
mkdir -p data
echo -e "${GREEN}✓ Data directory created${NC}"

echo ""
echo -e "${BLUE}4. Enabling and starting service...${NC}"

systemctl daemon-reload
systemctl enable whitelabel1

echo ""
echo -e "${YELLOW}Do you want to start the bot now? (y/n)${NC}"
read -r response

if [[ "$response" == "y" ]]; then
    systemctl start whitelabel1
    sleep 2
    
    if systemctl is-active --quiet whitelabel1; then
        echo -e "${GREEN}✅ Bot started successfully!${NC}"
        echo ""
        echo -e "${BLUE}📊 Service Status:${NC}"
        systemctl status whitelabel1 --no-pager
    else
        echo -e "${RED}❌ Bot failed to start${NC}"
        echo ""
        echo -e "${YELLOW}Check logs:${NC}"
        journalctl -u whitelabel1 -n 50 --no-pager
    fi
else
    echo -e "${YELLOW}⚠️  Bot not started. Start manually with:${NC}"
    echo "   sudo systemctl start whitelabel1"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "  • Start bot:    sudo systemctl start whitelabel1"
echo "  • Stop bot:     sudo systemctl stop whitelabel1"
echo "  • Restart bot:  sudo systemctl restart whitelabel1"
echo "  • Check status: sudo systemctl status whitelabel1"
echo "  • View logs:    sudo journalctl -u whitelabel1 -f"
echo "  • Edit config:  nano '$BOT_DIR/.env'"
echo ""
