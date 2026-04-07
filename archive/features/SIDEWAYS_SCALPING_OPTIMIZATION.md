# Sideways Scalping Optimization - Peningkatan Frekuensi Entry

## Tanggal: 2026-04-05

## Problem Statement

Bot scalping hanya melakukan entry pada 1 pair saja ketika market dalam kondisi sideways, padahal logic sideways detection sudah terpasang dengan benar. Hal ini disebabkan oleh kombinasi dari:

1. Cooldown period yang terlalu lama (5 menit)
2. Kriteria confidence yang terlalu ketat (75%)
3. Range width threshold yang terlalu sempit (max 3%)
4. Jumlah pairs yang terbatas (10 pairs)

## Solution Implemented

Menerapkan 4 optimasi untuk meningkatkan frekuensi entry di market sideways:

### 1. Reduced Cooldown Period ⏱️

**File:** `Bismillah/app/trading_mode.py`

```python
# BEFORE
cooldown_seconds: int = 300  # 5 minutes

# AFTER
cooldown_seconds: int = 150  # 2.5 minutes (50% reduction)
```

**Impact:** Pair yang sudah entry bisa di-scan lagi lebih cepat untuk opportunity baru.

### 2. Relaxed Confidence Threshold 📊

**File:** `Bismillah/app/scalping_engine.py`

```python
# BEFORE
if confidence < 75:
    return None

# AFTER
if confidence < 70:  # Relaxed for sideways
    return None
```

**Impact:** Lebih banyak sinyal sideways yang lolos validasi confidence.

### 3. Expanded Range Width Threshold 📏

**File:** `Bismillah/app/range_analyzer.py`

```python
# BEFORE
MAX_RANGE_PCT = 0.030  # 3.0%

# AFTER
MAX_RANGE_PCT = 0.040  # 4.0% (33% expansion)
```

**Impact:** Range yang lebih lebar (3-4%) tetap dianggap valid untuk sideways trading.

### 4. Added Volatile Pairs 🎯

**File:** `Bismillah/app/trading_mode.py`

```python
# BEFORE (10 pairs)
pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
         "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT"]

# AFTER (13 pairs)
pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
         "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
         "LINKUSDT", "UNIUSDT", "ATOMUSDT"]  # +3 volatile pairs
```

**Impact:** Lebih banyak pairs yang di-scan = lebih banyak opportunity sideways.

**Bonus:** Updated `MIN_QTY_MAP` untuk support pair baru:
```python
"LINKUSDT": 0.1, "UNIUSDT": 0.1, "ATOMUSDT": 0.1
```

## Expected Results

### Before Optimization
- Cooldown: 5 menit per pair
- Confidence threshold: 75%
- Range width: 0.5% - 3.0%
- Pairs: 10
- **Typical behavior:** 1 entry per sideways market

### After Optimization
- Cooldown: 2.5 menit per pair (50% faster)
- Confidence threshold: 70% (5% more lenient)
- Range width: 0.5% - 4.0% (33% wider acceptance)
- Pairs: 13 (30% more opportunities)
- **Expected behavior:** 2-4 concurrent entries per sideways market

## Risk Management

Semua optimasi tetap dalam batas aman:

✅ **Max concurrent positions:** Tetap 4 (tidak berubah)
✅ **Circuit breaker:** Tetap 5% daily loss limit
✅ **Max hold time:** Tetap 2 menit untuk sideways
✅ **R:R minimum:** Tetap 1.0
✅ **SL placement:** Tetap 0.15% di luar range

## Testing Recommendations

1. Monitor jumlah entry per jam di market sideways
2. Track win rate untuk confidence 70-75% range
3. Observe apakah range 3-4% width menghasilkan R:R yang baik
4. Validate pair baru (LINK, UNI, ATOM) memiliki liquidity yang cukup

## Files Modified

1. `Bismillah/app/trading_mode.py` - Cooldown & pairs config
2. `Bismillah/app/scalping_engine.py` - Confidence threshold & MIN_QTY_MAP
3. `Bismillah/app/range_analyzer.py` - Range width threshold

## Deployment Notes

- ✅ No database migration required
- ✅ No API changes
- ✅ Backward compatible
- ✅ Can be deployed without restart (config hot-reload)

## Monitoring Metrics

Track these metrics post-deployment:

```sql
-- Sideways trades per hour
SELECT 
  DATE_TRUNC('hour', opened_at) as hour,
  COUNT(*) as sideways_trades
FROM autotrade_trades
WHERE trade_subtype = 'sideways_scalp'
  AND opened_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;

-- Win rate by confidence range
SELECT 
  CASE 
    WHEN confidence BETWEEN 70 AND 74 THEN '70-74%'
    WHEN confidence BETWEEN 75 AND 79 THEN '75-79%'
    WHEN confidence >= 80 THEN '80%+'
  END as confidence_range,
  COUNT(*) as total_trades,
  SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
  ROUND(AVG(pnl_usdt), 2) as avg_pnl
FROM autotrade_trades
WHERE trade_subtype = 'sideways_scalp'
  AND closed_at IS NOT NULL
GROUP BY confidence_range;

-- Performance by pair (new pairs)
SELECT 
  symbol,
  COUNT(*) as trades,
  SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
  ROUND(AVG(pnl_usdt), 2) as avg_pnl
FROM autotrade_trades
WHERE symbol IN ('LINKUSDT', 'UNIUSDT', 'ATOMUSDT')
  AND trade_subtype = 'sideways_scalp'
GROUP BY symbol;
```

## Rollback Plan

Jika performa menurun, rollback dengan mengembalikan nilai:

```python
# trading_mode.py
cooldown_seconds: int = 300  # Back to 5 min
pairs: List[str] = [...10 pairs only...]  # Remove LINK, UNI, ATOM

# scalping_engine.py
if confidence < 75:  # Back to 75%

# range_analyzer.py
MAX_RANGE_PCT = 0.030  # Back to 3.0%
```

---

**Status:** ✅ Deployed
**Author:** Kiro AI Assistant
**Approved by:** User
