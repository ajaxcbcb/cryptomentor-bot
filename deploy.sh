#!/bin/bash
#
# CryptoMentor v2.2.0 VPS Deployment Script
# Automated deployment of coordinator + analytics to production
#
# Usage: bash deploy.sh
#

set -e  # Exit on error

echo "================================================================================"
echo "                   CryptoMentor v2.2.0 VPS Deployment"
echo "================================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/cryptomentor"
VENV_DIR="${PROJECT_DIR}/venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"

# ============================================================================
# STEP 1: Verify Prerequisites
# ============================================================================
echo -e "${YELLOW}[1/8]${NC} Verifying prerequisites..."

if ! command -v git &> /dev/null; then
    echo -e "${RED}ERROR: git not installed${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Git and Python3 found"
echo ""

# ============================================================================
# STEP 2: Pull Latest Code
# ============================================================================
echo -e "${YELLOW}[2/8]${NC} Pulling latest code from main branch..."

cd "${PROJECT_DIR}"

# Ensure we're on main branch
git fetch origin
git checkout main
git pull origin main

echo -e "${GREEN}✓${NC} Code updated to latest main branch"
echo ""

# ============================================================================
# STEP 3: Setup Python Virtual Environment
# ============================================================================
echo -e "${YELLOW}[3/8]${NC} Setting up Python virtual environment..."

if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

source "${VENV_DIR}/bin/activate"
echo ""

# ============================================================================
# STEP 4: Install Dependencies
# ============================================================================
echo -e "${YELLOW}[4/8]${NC} Installing Python dependencies..."

# Upgrade pip
"${PIP_BIN}" install --upgrade pip setuptools wheel --quiet

# Install requirements
"${PIP_BIN}" install -r requirements.txt --quiet

echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# ============================================================================
# STEP 5: Verify Environment Variables
# ============================================================================
echo -e "${YELLOW}[5/8]${NC} Verifying environment variables..."

if [ -z "$ADMIN_IDS" ] && [ -z "$ADMIN1" ]; then
    echo -e "${RED}WARNING: ADMIN_IDS not set${NC}"
    echo "         Set ADMIN_IDS or ADMIN1-5 environment variables"
    echo "         See .env file or systemd service"
fi

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo -e "${RED}WARNING: SUPABASE_URL or SUPABASE_KEY not set${NC}"
    echo "         These are required for analytics to function"
fi

if [ -z "$JWT_SECRET" ]; then
    echo -e "${YELLOW}⚠${NC}  JWT_SECRET not set (using default: analytics-secret-key)"
fi

echo -e "${GREEN}✓${NC} Environment variables checked"
echo ""

# ============================================================================
# STEP 6: Run Tests
# ============================================================================
echo -e "${YELLOW}[6/8]${NC} Running test suite..."

"${PYTHON_BIN}" -m pytest tests/test_coordinator.py tests/test_regression.py -v --tb=short 2>&1 | tail -20

echo -e "${GREEN}✓${NC} Tests completed"
echo ""

# ============================================================================
# STEP 7: Kill Existing Services
# ============================================================================
echo -e "${YELLOW}[7/8]${NC} Stopping existing services..."

# Kill analytics API if running
pkill -f "uvicorn.*analytics_api" || true
echo -e "${GREEN}✓${NC} Analytics API stopped (if running)"

# Note: Don't kill bot here - user should restart separately
echo -e "${GREEN}✓${NC} Services prepared for restart"
echo ""

# ============================================================================
# STEP 8: Start Analytics API
# ============================================================================
echo -e "${YELLOW}[8/8]${NC} Starting analytics API on port 8896..."

# Create systemd service if not exists
if [ ! -f "/etc/systemd/system/cryptomentor-analytics.service" ]; then
    echo "Creating systemd service..."
    sudo bash -c 'cat > /etc/systemd/system/cryptomentor-analytics.service << EOF
[Unit]
Description=CryptoMentor Analytics API
After=network.target

[Service]
Type=simple
User=cryptomentor
WorkingDirectory=/opt/cryptomentor
Environment="PATH=/opt/cryptomentor/venv/bin"
EnvironmentFile=/opt/cryptomentor/.env
ExecStart=/opt/cryptomentor/venv/bin/uvicorn Bismillah.analytics_api:app --host 0.0.0.0 --port 8896
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF'
    echo -e "${GREEN}✓${NC} Systemd service created"
fi

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cryptomentor-analytics
sudo systemctl start cryptomentor-analytics

sleep 2

# Verify it's running
if sudo systemctl is-active --quiet cryptomentor-analytics; then
    echo -e "${GREEN}✓${NC} Analytics API started successfully"
else
    echo -e "${RED}ERROR: Analytics API failed to start${NC}"
    sudo systemctl status cryptomentor-analytics
    exit 1
fi

echo ""

# ============================================================================
# STEP 9: Post-Deployment Verification
# ============================================================================
echo -e "${YELLOW}[9/9]${NC} Running post-deployment verification..."

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8896/health)
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓${NC} Health check passed: $HEALTH_RESPONSE"
else
    echo -e "${RED}ERROR: Health check failed${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Deployment Complete
# ============================================================================
echo "================================================================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo "================================================================================"
echo ""
echo "Analytics API:"
echo "  • Running on: http://localhost:8896"
echo "  • Dashboard: https://analytics4896.cryptomentor.id"
echo "  • Systemd: cryptomentor-analytics"
echo "  • Logs: sudo journalctl -u cryptomentor-analytics -f"
echo ""
echo "Next Steps:"
echo "  1. Restart Telegram bot: pkill -f 'python.*bot.py' && python Bismillah/bot.py &"
echo "  2. Monitor logs: sudo journalctl -u cryptomentor-analytics -f"
echo "  3. Verify coordinator behavior in production"
echo "  4. Team validates no false positives"
echo "  5. Monitor error rates for 1 hour"
echo ""
echo "Health Check:"
echo "  curl http://localhost:8896/health"
echo ""
echo "Troubleshooting:"
echo "  See DEPLOYMENT.md for complete guide"
echo ""
