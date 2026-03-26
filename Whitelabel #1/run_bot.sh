#!/bin/bash
# Script untuk menjalankan Whitelabel #1 Bot

# Warna untuk output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Whitelabel #1 Bot...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure it.${NC}"
    exit 1
fi

# Check if bot is already running
if pgrep -f "python.*bot.py" > /dev/null; then
    echo -e "${YELLOW}Bot is already running!${NC}"
    echo -e "PID: $(pgrep -f 'python.*bot.py')"
    exit 0
fi

# Run bot
echo -e "${GREEN}Bot starting in DEV MODE...${NC}"
python3 bot.py

echo -e "${RED}Bot stopped.${NC}"
