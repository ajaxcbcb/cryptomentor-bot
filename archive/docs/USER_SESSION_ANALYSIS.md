# User Session Analysis - April 3, 2026

## Current Status (16:02 CEST)

✅ **Active Sessions**: 9 users  
❌ **Inactive Sessions**: Unknown (need database access)  
🔄 **Auto-Restore**: Working perfectly

## Active Users (Currently Running)

1. User 1234500018 - 15 USDT, 10x leverage, Scalping
2. User 1234500011 - 10 USDT, 10x leverage, Scalping
3. User 1234500007 - 10 USDT, 20x leverage, Scalping
4. User 6954315669 - 14.5 USDT, 5x leverage, Scalping
5. User 1234500010 - 15 USDT, 20x leverage, Scalping
6. User 1234500006 - 25 USDT, 20x leverage, Scalping
7. User 1234500019 - 25 USDT, 50x leverage, **Swing** (manual mode)
8. User 1234500016 - 18 USDT, 10x leverage, Scalping
9. User 1234500017 - 10 USDT, 5x leverage, Scalping

## Historical Trend (Today)

| Time | Active Sessions | Change |
|------|----------------|--------|
| 08:29 | 13 | - |
| 12:18 | 12 | -1 user |
| 12:48 | 11 | -1 user |
| 16:02 | 9 | -2 users |

## Analysis

### Why Only 9 Active Sessions?

**Possible Reasons:**

1. **Users Stopped Manually** ✅ Most Likely
   - Users can stop their engines anytime via /autotrade
   - 4 users stopped throughout the day (13 → 9)
   - This is normal user behavior

2. **Insufficient Balance** ⚠️ Possible
   - Some users may have run out of balance
   - Engine auto-stops when balance too low
   - Need to check trade history for losses

3. **API Key Issues** ⚠️ Possible
   - Some users' API keys may have expired
   - Exchange may have revoked keys
   - Need to check error logs

4. **Circuit Breaker Triggered** ⚠️ Possible
   - Daily loss limit (5%) may have been hit
   - Engine auto-stops for safety
   - Need to check PnL data

### Total Registered Users

**Cannot determine without database access**, but based on patterns:
- Minimum: 13 users (peak today)
- Likely: 15-20 users (including inactive)
- Need to query `autotrade_sessions` table for exact count

## Recommendations

### 1. Query Database Directly
```sql
-- Get total registered users
SELECT COUNT(*) as total_users FROM autotrade_sessions;

-- Get active vs inactive breakdown
SELECT status, COUNT(*) as count 
FROM autotrade_sessions 
GROUP BY status;

-- Get users who stopped today
SELECT telegram_id, status, updated_at 
FROM autotrade_sessions 
WHERE status != 'active' 
AND updated_at >= '2026-04-03 00:00:00';
```

### 2. Check Why Users Stopped
- Review logs for "Engine stopped" messages
- Check if users manually stopped or auto-stopped
- Identify if there are systematic issues

### 3. Re-engage Inactive Users
- Send reminder notifications
- Offer support for issues
- Check if they need help with setup

## Auto-Restore Verification

✅ **Working Perfectly**
- All 9 active sessions restored on restart
- 0 failures
- Engines started within 3 seconds
- Users notified of restoration

## Next Steps

1. **Get database access** to query exact user counts
2. **Check logs** for why 4 users stopped today
3. **Monitor** if more users stop (pattern analysis)
4. **Re-engage** inactive users with reminders

---

**Note**: The decrease from 13 → 9 users is likely normal churn. Users test the bot, some continue, some stop. This is expected behavior for any trading bot service.
