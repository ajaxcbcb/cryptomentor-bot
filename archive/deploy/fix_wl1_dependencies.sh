#!/bin/bash

echo "=========================================="
echo "Fix Whitelabel #1 Dependencies"
echo "=========================================="
echo ""

VPS_HOST="147.93.156.165"
VPS_USER="root"
WL1_DIR="/root/cryptomentor-bot/whitelabel-1"

echo "Step 1: Check if venv exists..."
ssh ${VPS_USER}@${VPS_HOST} "ls -la ${WL1_DIR}/venv/bin/python 2>&1"

echo ""
echo "Step 2: Install httpx in venv (required for license_guard.py)..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && source venv/bin/activate && pip install httpx"

echo ""
echo "Step 3: Verify httpx installed..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && source venv/bin/activate && python -c 'import httpx; print(\"httpx version:\", httpx.__version__)'"

echo ""
echo "Step 4: Check .env file has correct values..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && cat .env | grep -E '(WL_ID|WL_SECRET_KEY|LICENSE_API_URL)'"

echo ""
echo "Step 5: Test license check from Python..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && source venv/bin/activate && python -c \"
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    wl_id = os.getenv('WL_ID')
    secret_key = os.getenv('WL_SECRET_KEY')
    api_url = os.getenv('LICENSE_API_URL')
    
    print(f'WL_ID: {wl_id}')
    print(f'SECRET_KEY: {secret_key}')
    print(f'API_URL: {api_url}')
    
    url = f'{api_url}/api/license/check'
    payload = {'wl_id': wl_id, 'secret_key': secret_key}
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        print(f'Status: {resp.status_code}')
        print(f'Response: {resp.json()}')

asyncio.run(test())
\""

echo ""
echo "Step 6: Restart whitelabel1 service..."
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl restart whitelabel1"

echo ""
echo "Step 7: Wait 5 seconds..."
sleep 5

echo ""
echo "Step 8: Check service status..."
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl status whitelabel1 --no-pager -l | head -20"

echo ""
echo "=========================================="
echo "✅ Fix completed!"
echo "=========================================="
echo ""
echo "Check logs with: ssh root@147.93.156.165 'sudo journalctl -u whitelabel1 -f'"
