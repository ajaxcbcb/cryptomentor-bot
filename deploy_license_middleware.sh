#!/bin/bash

# Deploy License Middleware to VPS
# This script pushes the middleware implementation and restarts the bot

set -e

echo "=================================================="
echo "  Deploy License Middleware to VPS"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# VPS details
VPS_IP="147.93.156.165"
VPS_USER="root"
PROJECT_DIR="/root/CryptoMentor-Telegram-Bot"

echo -e "${YELLOW}Step 1: Commit and push changes to GitHub${NC}"
git add "Whitelabel #1/app/license_guard.py"
git add "Whitelabel #1/app/license_middleware.py"
git add "Whitelabel #1/bot.py"
git add "test_license_middleware.py"
git add "LICENSE_MIDDLEWARE_IMPLEMENTATION.md"
git add "deploy_license_middleware.sh"

git commit -m "feat: Add license middleware to block users when admin hasn't paid

- Added check_license_valid() method to LicenseGuard
- Created LicenseMiddleware to check license before processing user updates
- Middleware blocks all user requests when license suspended
- Admin access preserved for troubleshooting
- 60-second cache to optimize performance
- User-friendly error messages
- Comprehensive test script and documentation"

git push origin main

echo -e "${GREEN}✅ Changes pushed to GitHub${NC}"
echo ""

echo -e "${YELLOW}Step 2: SSH to VPS and pull changes${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
set -e

cd /root/CryptoMentor-Telegram-Bot

echo "Pulling latest changes..."
git pull origin main

echo ""
echo "✅ Changes pulled successfully"
echo ""

echo "Restarting whitelabel-1 bot..."
systemctl restart whitelabel-1

echo ""
echo "Waiting 3 seconds for bot to start..."
sleep 3

echo ""
echo "Checking bot status..."
systemctl status whitelabel-1 --no-pager -l

echo ""
echo "=================================================="
echo "  Deployment Complete!"
echo "=================================================="
echo ""
echo "📋 Verification Steps:"
echo ""
echo "1. Check logs for middleware registration:"
echo "   journalctl -u whitelabel-1 -n 50 --no-pager | grep -i middleware"
echo ""
echo "2. Test with regular user (should work if license active)"
echo ""
echo "3. To test blocking behavior:"
echo "   - Set balance to \$0 in database"
echo "   - Try to use bot as regular user → should be blocked"
echo "   - Try to use bot as admin → should work"
echo ""
echo "4. View live logs:"
echo "   journalctl -u whitelabel-1 -f"
echo ""

ENDSSH

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the bot with a regular user account"
echo "2. Verify middleware is blocking when license suspended"
echo "3. Check that admin can still access when suspended"
echo ""
