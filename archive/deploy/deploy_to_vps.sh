#!/bin/bash
# Deployment script untuk push ke VPS Contabo
# Usage: ./deploy_to_vps.sh [vps_ip] [vps_user]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VPS_IP="${1:-147.93.156.165}"
VPS_USER="${2:-root}"
VPS_PATH="/root/cryptomentor-bot"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  CryptoMentor Bot - VPS Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Target VPS:${NC} ${VPS_USER}@${VPS_IP}"
echo -e "${YELLOW}Remote Path:${NC} ${VPS_PATH}"
echo ""

# Check if git is clean
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes. Commit first? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        echo -e "${BLUE}📝 Committing changes...${NC}"
        git add .
        echo "Enter commit message:"
        read -r commit_msg
        git commit -m "$commit_msg"
    fi
fi

# Push to git
echo -e "${BLUE}📤 Pushing to git repository...${NC}"
git push origin main || git push origin master

# Deploy to VPS
echo ""
echo -e "${BLUE}🚀 Deploying to VPS...${NC}"
echo ""

ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
set -e

# Colors for remote
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd /root/cryptomentor-bot

echo -e "${BLUE}📥 Pulling latest changes...${NC}"
git stash
git pull origin main || git pull origin master
git stash pop || true

echo ""
echo -e "${BLUE}🔧 Installing dependencies...${NC}"

# Install Bismillah dependencies
cd Bismillah
pip3 install -r requirements.txt --quiet

# Install Whitelabel #1 dependencies
cd "../Whitelabel #1"
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt --quiet
fi

# Install license server dependencies
cd ../license_server
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt --quiet
fi

cd ..

echo ""
echo -e "${BLUE}🔄 Restarting services...${NC}"

# Restart main bot
if systemctl is-active --quiet cryptomentor; then
    echo -e "${YELLOW}  ↻ Restarting CryptoMentor bot...${NC}"
    systemctl restart cryptomentor
    sleep 2
    if systemctl is-active --quiet cryptomentor; then
        echo -e "${GREEN}  ✓ CryptoMentor bot restarted${NC}"
    else
        echo -e "${RED}  ✗ CryptoMentor bot failed to start${NC}"
        systemctl status cryptomentor --no-pager -l
    fi
else
    echo -e "${YELLOW}  ⚠ CryptoMentor bot not running${NC}"
fi

# Restart whitelabel bot
if systemctl is-active --quiet whitelabel1; then
    echo -e "${YELLOW}  ↻ Restarting Whitelabel #1 bot...${NC}"
    systemctl restart whitelabel1
    sleep 2
    if systemctl is-active --quiet whitelabel1; then
        echo -e "${GREEN}  ✓ Whitelabel #1 bot restarted${NC}"
    else
        echo -e "${RED}  ✗ Whitelabel #1 bot failed to start${NC}"
        systemctl status whitelabel1 --no-pager -l
    fi
else
    echo -e "${YELLOW}  ⚠ Whitelabel #1 bot not running${NC}"
fi

# Restart license server
if systemctl is-active --quiet license-server; then
    echo -e "${YELLOW}  ↻ Restarting License Server...${NC}"
    systemctl restart license-server
    sleep 2
    if systemctl is-active --quiet license-server; then
        echo -e "${GREEN}  ✓ License Server restarted${NC}"
    else
        echo -e "${RED}  ✗ License Server failed to start${NC}"
        systemctl status license-server --no-pager -l
    fi
else
    echo -e "${YELLOW}  ⚠ License Server not running${NC}"
fi

echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo ""
systemctl status cryptomentor whitelabel1 license-server --no-pager | grep -E "Active:|Main PID:" || true

echo ""
echo -e "${GREEN}✅ Deployment completed!${NC}"

ENDSSH

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Deployment Successful!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo "  • Check logs: ssh ${VPS_USER}@${VPS_IP} 'journalctl -u whitelabel1 -f'"
echo "  • Test bot: Send /start to @WL#1 bot"
echo ""
