# BingX Balance Display Fix

## Masalah yang Diperbaiki

User BingX setelah setup API Key tidak bisa melihat balance mereka di Telegram dengan format yang sama seperti Bitunix.

## Root Cause

1. **Missing `balance` field**: BingX client hanya mengembalikan `available` dan `equity`, tidak ada field `balance` yang digunakan oleh handler Telegram
2. **Missing `pnl` field**: Positions dari BingX tidak memiliki field `pnl` yang digunakan untuk menampilkan profit/loss
3. **Missing `mark_price` field**: Positions tidak memiliki `mark_price` untuk kalkulasi PnL percentage
4. **Inconsistent `side` format**: BingX menggunakan "LONG"/"SHORT" sedangkan handler mengharapkan "BUY"/"SELL"
5. **Hardcoded exchange name**: Message "Exchange: BITUNIX" hardcoded, tidak dinamis berdasarkan exchange user

## Solusi yang Diterapkan

### 1. Update BingX Client - `get_account_info()`

**File**: `Bismillah/app/bingx_autotrade_client.py`

```python
def get_account_info(self) -> Dict:
    """Get futures account balance."""
    res = self._request("GET", "/openApi/swap/v2/user/balance", signed=True)
    if not res["success"]:
        return res
    data = res["data"] or {}
    balance_data = data.get("balance", {})
    available = float(balance_data.get("availableMargin", 0))
    equity    = float(balance_data.get("equity", 0))
    unrealized = float(balance_data.get("unrealizedProfit", 0))
    return {
        "success":              True,
        "balance":              equity,  # ✅ Tambahkan field 'balance' untuk konsistensi
        "available":            available,
        "equity":               equity,
        "total_unrealized_pnl": unrealized,
        "raw":                  data,
    }
```

**Perubahan**:
- ✅ Tambahkan field `balance` yang berisi nilai `equity`
- ✅ Konsisten dengan format response Bitunix client

### 2. Update BingX Client - `get_positions()`

**File**: `Bismillah/app/bingx_autotrade_client.py`

```python
def get_positions(self) -> Dict:
    """Get all open positions."""
    res = self._request("GET", "/openApi/swap/v2/user/positions", signed=True)
    if not res["success"]:
        return res
    positions = []
    for p in (res["data"] or []):
        qty = float(p.get("positionAmt", 0))
        if qty == 0:
            continue
        
        entry_price = float(p.get("avgPrice", 0))
        mark_price = float(p.get("markPrice", 0))
        unrealized_pnl = float(p.get("unrealizedProfit", 0))
        
        positions.append({
            "symbol":         p.get("symbol", ""),
            "side":           "BUY" if qty > 0 else "SELL",  # ✅ Gunakan BUY/SELL
            "size":           abs(qty),
            "entry_price":    entry_price,
            "mark_price":     mark_price,                    # ✅ Tambahkan mark_price
            "pnl":            unrealized_pnl,                # ✅ Tambahkan field 'pnl'
            "unrealized_pnl": unrealized_pnl,
            "leverage":       int(p.get("leverage", 1)),
            "margin_mode":    p.get("marginType", "cross").lower(),
        })
    return {"success": True, "positions": positions}
```

**Perubahan**:
- ✅ Ubah `side` dari "LONG"/"SHORT" menjadi "BUY"/"SELL" untuk konsistensi
- ✅ Tambahkan field `mark_price` dari API response
- ✅ Tambahkan field `pnl` yang berisi `unrealized_pnl`
- ✅ Format response konsisten dengan Bitunix client

### 3. Fix Hardcoded Exchange Name

**File**: `Bismillah/app/handlers_autotrade.py`

**Before**:
```python
f"🏦 Exchange: BITUNIX\n\n"
```

**After**:
```python
f"🏦 Exchange: {ex_cfg['name']}\n\n"
```

**Perubahan**:
- ✅ Exchange name sekarang dinamis berdasarkan exchange yang dipilih user
- ✅ BingX akan menampilkan "BingX", Bitunix akan menampilkan "Bitunix"

## Format Tampilan di Telegram

Setelah perbaikan, balance BingX akan ditampilkan dengan format yang sama seperti Bitunix:

```
📊 Portfolio Status

⚙️ Engine: 🟢 Active
💰 Balance: 1025.80 USDT
📈 Unrealized PnL: +25.30 USDT
🔄 Open positions: 2

📋 Active Positions:

🟢 BTC BUY 10x
  📍 Entry: 45000.0000
  💹 Mark:  45500.0000
  📦 Size:  0.05
  📈 PnL: +25.0000 USDT (+1.11%)

🔴 ETH SELL 20x
  📍 Entry: 2500.0000
  💹 Mark:  2480.0000
  📦 Size:  2.5
  📈 PnL: +50.0000 USDT (+0.80%)

⏱ Updated: 17:45:30
```

## Testing

### Test 1: Response Format
```bash
python test_bingx_balance_display.py
```

**Result**: ✅ PASSED
- BingX account info format correct
- BingX positions format correct
- Telegram display format correct

### Test 2: Integration Test
```bash
# Di bot Telegram:
1. /autotrade
2. Pilih BingX
3. Setup API Key
4. Start Trading
5. Klik "📊 Status Portfolio"
```

**Expected Result**:
- ✅ Balance ditampilkan dengan benar
- ✅ Unrealized PnL ditampilkan
- ✅ Open positions ditampilkan dengan detail lengkap
- ✅ Format sama persis dengan Bitunix

## Compatibility

Perbaikan ini **backward compatible** dengan Bitunix dan exchange lainnya:

| Exchange | Balance Display | Positions Display | Status |
|----------|----------------|-------------------|--------|
| Bitunix  | ✅ Working     | ✅ Working        | ✅ OK  |
| BingX    | ✅ Fixed       | ✅ Fixed          | ✅ OK  |
| Binance  | ⏳ Coming Soon | ⏳ Coming Soon    | 🔜     |
| Bybit    | ⏳ Coming Soon | ⏳ Coming Soon    | 🔜     |

## Files Modified

1. ✅ `Bismillah/app/bingx_autotrade_client.py`
   - Updated `get_account_info()` to include `balance` field
   - Updated `get_positions()` to include `pnl` and `mark_price` fields
   - Changed `side` format from LONG/SHORT to BUY/SELL

2. ✅ `Bismillah/app/handlers_autotrade.py`
   - Fixed hardcoded "BITUNIX" to use dynamic `ex_cfg['name']`

3. ✅ `test_bingx_balance_display.py` (new)
   - Comprehensive test untuk memverifikasi format response
   - Test tampilan di Telegram

## Deployment Checklist

- [x] Update BingX client response format
- [x] Fix hardcoded exchange name
- [x] Create test file
- [x] Run tests
- [x] Verify backward compatibility
- [ ] Deploy to VPS
- [ ] Test dengan real BingX account
- [ ] Monitor for errors

## Next Steps

1. Deploy ke VPS production
2. Test dengan real BingX API credentials
3. Monitor user feedback
4. Prepare untuk Binance & Bybit integration

---

**Status**: ✅ COMPLETED
**Date**: 2026-03-31
**Tested**: ✅ Local tests passed
