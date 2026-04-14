#!/bin/bash
# Deploy script untuk dijalankan di VPS
# Usage: ./deploy_frontend.sh [source_dir]

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SOURCE_DIR="${1:-.}"
DEST_DIR="/root/cryptomentor-bot/website-frontend/dist"
BACKUP_DIR="/root/cryptomentor-bot/website-frontend/dist.backup.$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🚀 DEPLOY FRONTEND CRYPTOMENTOR${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if source exists
if [ ! -d "$SOURCE_DIR/dist" ]; then
    echo -e "${RED}✗ Directory $SOURCE_DIR/dist tidak ditemukan!${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Source: $SOURCE_DIR/dist${NC}"
echo -e "${YELLOW}📁 Destination: $DEST_DIR${NC}"
echo ""

# Step 1: Backup existing
if [ -d "$DEST_DIR" ]; then
    echo -e "${YELLOW}💾 Backup existing dist...${NC}"
    mkdir -p /root/cryptomentor-bot/website-frontend
    cp -r "$DEST_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
    echo ""
fi

# Step 2: Deploy files
echo -e "${YELLOW}📤 Deploying files...${NC}"
mkdir -p "$DEST_DIR"

# Copy all files with progress
rsync -av --delete "$SOURCE_DIR/dist/" "$DEST_DIR/" 2>&1 | grep -E "(^building|^deleting|^sent|files/s)" || true

FILE_COUNT=$(find "$DEST_DIR" -type f | wc -l)
echo -e "${GREEN}✓ Deployed $FILE_COUNT files${NC}"
echo ""

# Step 3: Verify
echo -e "${YELLOW}✅ Verifying...${NC}"
if [ -f "$DEST_DIR/index.html" ]; then
    echo -e "${GREEN}✓ index.html found${NC}"
    ls -lah "$DEST_DIR/index.html"
else
    echo -e "${RED}✗ index.html NOT found!${NC}"
    exit 1
fi

echo ""

# Step 4: Reload nginx
echo -e "${YELLOW}🔄 Reloading nginx...${NC}"
if sudo systemctl reload nginx; then
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
else
    echo -e "${YELLOW}⚠ Nginx reload failed (check status)${NC}"
fi

echo ""

# Step 5: Clear browser cache (nginx headers)
echo -e "${YELLOW}🗑 Cache control headers set${NC}"
grep -i "cache-control" /etc/nginx/sites-available/www-cryptomentor.conf 2>/dev/null || echo "  (Check nginx config)"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ DEPLOY SELESAI!${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🌐 URL: https://cryptomentor.id${NC}"
echo -e "${BLUE}📊 Files: $FILE_COUNT${NC}"
echo -e "${BLUE}💾 Backup: $BACKUP_DIR${NC}"
echo ""
