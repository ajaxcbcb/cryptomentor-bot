# Bitunix TP Partial & SL BEP Implementation Specification

## Overview
Implementasi fitur TP Partial (Take Profit Partial) dan SL BEP (Stop Loss Break Even Point) menggunakan Bitunix API `modify_position_tp_sl_order`.

## API Documentation Summary

### Endpoint
```
POST /api/v1/futures/tpsl/position/modify_order
```

### Rate Limit
10 requests/second/UID

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair (e.g., "BTCUSDT") |
| positionId | string | Yes | Position ID associated with TP/SL |
| tpPrice | string | No | Take-profit trigger price |
| tpStopType | string | No | TP trigger type: LAST_PRICE or MARK_PRICE (default) |
| slPrice | string | No | Stop-loss trigger price |
| slStopType | string | No | SL trigger type: LAST_PRICE or MARK_PRICE (default) |

**Note:** At least one of `tpPrice` or `slPrice` is required.

### Response
```json
{
  "code": 0,
  "data": {
    "orderId": "11111"
  },
  "msg": "Success"
}
```

## Feature Requirements

### 1. TP Partial (Take Profit Partial)
**Goal:** Close 50% of position at TP1, let remaining 50% run to TP2

**Flow:**
1. Entry: Open position with full size
2. TP1 Hit (50%): Close 50% of position, move SL to breakeven
3. TP2 Target: Let remaining 50% run to higher target

**Example:**
- Entry: 100 USDT position
- TP1 (1:1.5 R:R): Close 50 USDT, lock 50% profit
- Move SL to entry price (breakeven)
- TP2 (1:3 R:R): Close remaining 50 USDT

### 2. SL BEP (Stop Loss Break Even Point)
**Goal:** Move SL to entry price after TP1 is hit to protect capital

**Flow:**
1. Position opens with initial SL
2. When TP1 is hit → Modify SL to entry price
3. Worst case: Break even (no loss)
4. Best case: TP2 hit for additional profit

## Implementation Strategy

### Phase 1: Add modify_tp_sl to Bitunix Client
Add new method to `bitunix_autotrade_client.py`:

```python
def modify_position_tp_sl(self, symbol: str, position_id: str, 
                         tp_price: float = None, sl_price: float = None,
                         tp_stop_type: str = "MARK_PRICE",
                         sl_stop_type: str = "MARK_PRICE") -> dict:
    """
    Modify TP/SL for existing position.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        position_id: Position ID from open position
        tp_price: New take-profit price (optional)
        sl_price: New stop-loss price (optional)
        tp_stop_type: "LAST_PRICE" or "MARK_PRICE" (default)
        sl_stop_type: "LAST_PRICE" or "MARK_PRICE" (default)
    
    Returns:
        {"success": True, "order_id": "xxx"} or {"success": False, "error": "..."}
    """
```

### Phase 2: Track Position IDs
Modify trade tracking to store `position_id`:

**Database Schema Update:**
```sql
ALTER TABLE autotrade_trades 
ADD COLUMN position_id TEXT,
ADD COLUMN tp1_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN sl_moved_to_bep BOOLEAN DEFAULT FALSE;
```

### Phase 3: Implement TP Partial Logic
Add to autotrade engine monitoring:

```python
async def _check_tp_partial(position):
    """Check if TP1 is hit and execute partial close."""
    
    # Calculate TP1 price (1:1.5 R:R)
    entry_price = position['entry_price']
    sl_price = position['sl_price']
    risk = abs(entry_price - sl_price)
    
    if position['side'] == 'LONG':
        tp1_price = entry_price + (risk * 1.5)
    else:
        tp1_price = entry_price - (risk * 1.5)
    
    # Check if current price >= TP1
    current_price = get_current_price(position['symbol'])
    
    if is_tp1_hit(current_price, tp1_price, position['side']):
        # Close 50% of position
        await close_partial_position(position, percent=50)
        
        # Move SL to breakeven
        await move_sl_to_breakeven(position)
        
        # Mark TP1 as hit
        mark_tp1_hit(position['id'])
```

### Phase 4: Implement SL BEP Logic
```python
async def move_sl_to_breakeven(position):
    """Move stop loss to entry price (breakeven)."""
    
    entry_price = position['entry_price']
    position_id = position['position_id']
    symbol = position['symbol']
    
    # Modify SL to entry price
    result = client.modify_position_tp_sl(
        symbol=symbol,
        position_id=position_id,
        sl_price=entry_price,
        sl_stop_type="MARK_PRICE"
    )
    
    if result['success']:
        # Update database
        update_sl_price(position['id'], entry_price)
        mark_sl_moved_to_bep(position['id'])
        
        # Notify user
        await notify_user(
            f"🛡️ SL moved to breakeven for {symbol}\n"
            f"Entry: {entry_price}\n"
            f"New SL: {entry_price} (Break Even)\n"
            f"Position is now risk-free!"
        )
```

## Risk Management Benefits

### Before (Current System)
- Entry → TP (1:2 R:R) or SL
- Win: +2R
- Loss: -1R
- Win rate needed: 33.3% to break even

### After (With TP Partial + SL BEP)
- Entry → TP1 (50% at 1:1.5) → SL to BEP → TP2 (50% at 1:3)
- Scenario 1: TP1 + TP2 hit = +0.75R + +1.5R = +2.25R
- Scenario 2: TP1 hit, TP2 stopped at BEP = +0.75R + 0R = +0.75R
- Scenario 3: SL hit before TP1 = -1R
- Win rate needed: 25% to break even (much better!)

### Psychological Benefits
- Reduced stress: Position becomes risk-free after TP1
- Better sleep: No worry about giving back profits
- Increased confidence: Locked profits + free runner

## Implementation Files

### 1. `bitunix_autotrade_client.py`
Add `modify_position_tp_sl()` method

### 2. `autotrade_engine.py` or `scalping_engine.py`
Add TP partial monitoring logic

### 3. Database Migration
```sql
-- db/add_tp_partial_tracking.sql
ALTER TABLE autotrade_trades 
ADD COLUMN IF NOT EXISTS position_id TEXT,
ADD COLUMN IF NOT EXISTS tp1_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS sl_moved_to_bep BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp1_price NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp2_price NUMERIC(18,8);
```

### 4. Configuration
Add to user settings:
- Enable/disable TP Partial
- TP1 R:R ratio (default 1:1.5)
- TP2 R:R ratio (default 1:3)
- Partial close percentage (default 50%)

## Testing Plan

### Unit Tests
1. Test `modify_position_tp_sl()` API call
2. Test TP1 price calculation
3. Test partial close logic
4. Test SL BEP modification

### Integration Tests
1. Open position → Wait for TP1 → Verify 50% closed
2. Verify SL moved to entry price
3. Verify remaining 50% runs to TP2
4. Test error handling (API failures, invalid position_id)

### Live Testing
1. Test with small position size (10 USDT)
2. Monitor TP1 trigger accuracy
3. Verify SL modification works
4. Check notification messages

## Deployment Strategy

### Phase 1: Backend Implementation (Week 1)
- Add API method to Bitunix client
- Add database columns
- Implement TP partial logic
- Implement SL BEP logic

### Phase 2: Testing (Week 2)
- Unit tests
- Integration tests
- Live testing with small positions

### Phase 3: UI/Settings (Week 3)
- Add TP Partial toggle in settings
- Add R:R ratio configuration
- Add partial close percentage setting

### Phase 4: Rollout (Week 4)
- Deploy to production
- Enable for premium users first
- Monitor performance
- Gradual rollout to all users

## Success Metrics

### Performance Metrics
- Win rate improvement
- Average R:R improvement
- Drawdown reduction
- User satisfaction

### Technical Metrics
- API success rate (>99%)
- TP1 detection accuracy (>95%)
- SL modification success rate (>99%)
- Average execution time (<2 seconds)

## Risks & Mitigation

### Risk 1: API Rate Limit
**Mitigation:** Queue modifications, max 10/sec

### Risk 2: Position ID Not Available
**Mitigation:** Fallback to manual close if position_id missing

### Risk 3: Partial Close Fails
**Mitigation:** Retry logic + alert admin

### Risk 4: SL Modification Fails
**Mitigation:** Keep original SL, notify user

## Future Enhancements

### V2 Features
- Multiple TP levels (TP1, TP2, TP3)
- Dynamic R:R based on market conditions
- Trailing stop after TP1
- Partial close at multiple levels (25%, 50%, 75%)

### V3 Features
- AI-powered TP level optimization
- Volatility-based R:R adjustment
- Time-based SL tightening
- Correlation-based position sizing

## Conclusion

TP Partial + SL BEP adalah game-changer untuk risk management. Fitur ini akan:
- Meningkatkan win rate efektif
- Mengurangi stress trading
- Melindungi profit yang sudah didapat
- Memberikan free runner untuk profit maksimal

Implementation complexity: Medium
Expected impact: High
Priority: High

---

**Next Steps:**
1. Review dan approve spec ini
2. Implement Phase 1 (Backend)
3. Test dengan position kecil
4. Deploy ke production
