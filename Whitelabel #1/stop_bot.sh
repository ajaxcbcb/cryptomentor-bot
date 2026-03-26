#!/bin/bash
# Script untuk menghentikan Whitelabel #1 Bot

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}Stopping Whitelabel #1 Bot...${NC}"

# Find and kill bot process
PID=$(pgrep -f "python.*bot.py")

if [ -z "$PID" ]; then
    echo -e "${GREEN}Bot is not running.${NC}"
    exit 0
fi

kill $PID
echo -e "${GREEN}Bot stopped (PID: $PID)${NC}"
