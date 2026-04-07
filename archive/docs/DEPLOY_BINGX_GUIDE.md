# Deploy BingX Updates to VPS - Guide

## Quick Deploy

### Option 1: PowerShell (Windows)
```powershell
.\deploy_bingx_to_vps.ps1
```

### Option 2: Bash (Linux/Mac/WSL)
```bash
chmod +x deploy_bingx_to_vps.sh
./deploy_bingx_to_vps.sh
```

## What Gets Deployed

### Modified Files
1. `Bismillah/app/exchange_registry.py`
   - Added `requires_uid_verification` flag
   - BingX configured without UID verification

2. `Bismillah/app/handlers_autotrade.py`
   - Fixed registration flow for BingX
   - Dynamic error messages per exchange
   - Pass `exchange_id` to autotrade engine

3. `Bismillah/app/bingx_autotrade_client.py`
   - Fixed `get_account_info()` response format
   - Fixed `get_positions()` response format
   - Added `balance`, `pnl`, `mark_price` fields

4. `Bismillah/app/autotrade_engine.py`
   - Multi-exchange support
   - Dynamic client creation via `get_client()`
   - Exchange-specific logging

5. `Bismillah/app/scheduler.py`
   - Auto-restore engine with exchange_id
   - Exchange-aware logging

## Deployment Process

### Step 1: Backup
Script automatically creates backup on VPS:
```
/root/CryptoMentor/backups/bingx_update_YYYYMMDD_HHMMSS/
```

### Step 2: Upload Files
All modified files uploaded via SCP/PSCP

### Step 3: Restart Service
Bot service restarted automatically:
```bash
systemctl stop cryptomentor-bot
systemctl start cryptomentor-bot
```

## Post-Deployment Verification

### 1. Check Service Status
```bash
ssh -p 22 root@147.93.156.165
systemctl status cryptomentor-bot
```

### 2. Monitor Logs
```bash
journalctl -u cryptomentor-bot -f
```

Look for:
- ✅ `Bot started successfully`
- ✅ `[Engine:XXX] Using exchange: BingX (bingx)`
- ❌ Any error messages

### 3. Test BingX Registration

**Via Telegram:**
1. Send `/autotrade` to bot
2. Select "BingX"
3. Should see API Key setup (no referral flow)
4. Input API Key & Secret
5. Should go directly to "Start Trading"
6. No UID verification prompt

### 4. Test BingX Balance Display

**Via Telegram:**
1. After setup, click "📊 Status Portfolio"
2. Should see:
   - Balance in USDT
   - Unrealized PnL
   - Open positions (if any)

### 5. Test BingX AutoTrade

**Via Telegram:**
1. Set trading amount & leverage
2. Click "🚀 Start Trading"
3. Check logs for:
   ```
   [Engine:XXX] PRO ENGINE STARTED
   [Engine:XXX] Using exchange: BingX (bingx)
   ```

## Rollback Procedure

If something goes wrong:

### 1. SSH to VPS
```bash
ssh -p 22 root@147.93.156.165
```

### 2. Find Backup
```bash
cd /root/CryptoMentor/backups
ls -la
# Find latest backup: bingx_update_YYYYMMDD_HHMMSS
```

### 3. Restore Files
```bash
cd /root/CryptoMentor
BACKUP_DIR="backups/bingx_update_YYYYMMDD_HHMMSS"

cp "$BACKUP_DIR/exchange_registry.py" Bismillah/app/
cp "$BACKUP_DIR/handlers_autotrade.py" Bismillah/app/
cp "$BACKUP_DIR/bingx_autotrade_client.py" Bismillah/app/
cp "$BACKUP_DIR/autotrade_engine.py" Bismillah/app/
cp "$BACKUP_DIR/scheduler.py" Bismillah/app/
```

### 4. Restart Service
```bash
systemctl restart cryptomentor-bot
systemctl status cryptomentor-bot
```

## Troubleshooting

### Issue: Bot won't start after deployment

**Check logs:**
```bash
journalctl -u cryptomentor-bot -n 100 --no-pager
```

**Common causes:**
- Syntax error in Python files
- Missing import statements
- Permission issues

**Solution:**
1. Check error message in logs
2. Fix the issue or rollback
3. Restart service

### Issue: BingX users can't register

**Check:**
1. `exchange_registry.py` has correct config
2. `requires_uid_verification: False` for BingX
3. No errors in bot logs

**Test manually:**
```bash
cd /root/CryptoMentor
python3 -c "
from Bismillah.app.exchange_registry import get_exchange
ex = get_exchange('bingx')
print(f'BingX requires UID: {ex.get(\"requires_uid_verification\", False)}')
"
```

Should output: `BingX requires UID: False`

### Issue: BingX balance not showing

**Check:**
1. BingX client response format
2. API credentials valid
3. Network connectivity to BingX API

**Test manually:**
```bash
cd /root/CryptoMentor
python3 -c "
from Bismillah.app.bingx_autotrade_client import BingXAutoTradeClient
client = BingXAutoTradeClient(api_key='<REDACTED_API_KEY>', api_secret='<REDACTED_API_SECRET>')
result = client.get_account_info()
print(result)
"
```

### Issue: AutoTrade engine not starting for BingX

**Check logs for:**
```
[Engine:XXX] Using exchange: BingX (bingx)
```

**If missing:**
1. Check `exchange_id` is passed to `start_engine()`
2. Check `get_client()` works for BingX
3. Check BingX client initialization

## Manual Deployment (Alternative)

If scripts don't work, deploy manually:

### 1. Upload Files via SCP
```bash
scp -P 22 Bismillah/app/exchange_registry.py root@147.93.156.165:/root/CryptoMentor/Bismillah/app/
scp -P 22 Bismillah/app/handlers_autotrade.py root@147.93.156.165:/root/CryptoMentor/Bismillah/app/
scp -P 22 Bismillah/app/bingx_autotrade_client.py root@147.93.156.165:/root/CryptoMentor/Bismillah/app/
scp -P 22 Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/CryptoMentor/Bismillah/app/
scp -P 22 Bismillah/app/scheduler.py root@147.93.156.165:/root/CryptoMentor/Bismillah/app/
```

### 2. SSH and Restart
```bash
ssh -p 22 root@147.93.156.165
cd /root/CryptoMentor
systemctl restart cryptomentor-bot
systemctl status cryptomentor-bot
```

## Success Indicators

✅ Bot service running
✅ No errors in logs
✅ BingX registration works (no UID prompt)
✅ BingX balance displays correctly
✅ BingX autotrade engine starts
✅ Existing Bitunix users unaffected

## Support

If issues persist:
1. Check all logs carefully
2. Verify file permissions
3. Test with demo BingX account
4. Contact for assistance

---

**VPS Details:**
- Host: 147.93.156.165
- Port: 22
- User: root
- Path: /root/CryptoMentor
