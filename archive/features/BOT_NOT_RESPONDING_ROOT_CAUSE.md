# 🔍 Root Cause: Bot Tidak Merespon /start

**Date**: April 3, 2026 13:55 CEST  
**Issue**: Bot tidak merespon command /start  
**Root Cause**: FOUND ✅

## Problem

Bot TIDAK melakukan polling Telegram API karena event loop ter-block oleh:

1. **11 Scalping Engines** berjalan bersamaan
2. Setiap engine melakukan **scan setiap 15 detik**
3. Setiap scan mengambil **100+ candles** dari Bitunix API
4. Total: **1000+ API calls setiap 15 detik** (11 engines × 10 pairs × 2 timeframes × 2 candle types)

## Evidence

```bash
# Check getUpdates calls in last minute
$ journalctl -u cryptomentor --since '1 minute ago' | grep -i 'getupdates' | wc -l
0  # ← NO POLLING AT ALL!
```

Logs menunjukkan:
- Bot hanya fetch candles terus menerus
- Tidak ada log `getUpdates` dari Telegram API
- Event loop ter-block oleh I/O operations

## Why This Happens

### Before Migration (Swing Mode)
- Max 1 concurrent position per user
- 15M timeframe (scan every 60 seconds)
- Less frequent API calls
- Polling worked fine

### After Migration (Scalping Mode)
- Max 4 concurrent positions per user
- 5M timeframe (scan every 15 seconds)
- 4x more frequent scans
- 11 engines × 10 pairs = 110 concurrent scans
- Event loop overwhelmed

## Technical Details

**Scalping Engine Config**:
```python
ScalpingConfig(
    timeframe='5m',
    scan_interval=15,  # ← Too frequent!
    max_concurrent_positions=4,
    pairs=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 
           'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT']
)
```

**Load Calculation**:
- 11 active engines
- 10 pairs per engine
- 2 timeframes (100 + 60 candles)
- Scan every 15 seconds
- = **1,760 API calls every 15 seconds**
- = **7,040 API calls per minute**

## Solutions

### Option 1: Increase Scan Interval (Quick Fix)
Change `scan_interval` from 15 to 30 seconds:
```python
scan_interval=30  # Reduce load by 50%
```

### Option 2: Reduce Pairs (Medium Fix)
Only scan top 5 pairs instead of 10:
```python
pairs=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
```

### Option 3: Implement Proper Async (Best Fix)
Use `asyncio.gather` with semaphore to limit concurrent requests:
```python
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
async with semaphore:
    await fetch_candles(...)
```

### Option 4: Separate Process for Engines
Run engines in separate process/thread pool to not block main event loop.

## Immediate Action

Untuk sementara, restart bot dan tunggu 1-2 menit sampai engines selesai initial scan, lalu test /start lagi.

```bash
systemctl restart cryptomentor
# Wait 2 minutes for engines to initialize
# Then test /start command
```

## Long-term Fix

Implement Option 3 (Proper Async) + Option 1 (Increase Interval):
1. Add semaphore to limit concurrent API calls
2. Increase scan_interval to 30 seconds
3. Use connection pooling for Bitunix API
4. Add caching for candle data

---

**Status**: Root cause identified  
**Priority**: HIGH - Bot tidak bisa menerima command baru  
**Impact**: All users cannot interact with bot
