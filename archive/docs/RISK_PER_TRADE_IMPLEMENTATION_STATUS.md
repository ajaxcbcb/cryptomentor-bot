# Risk Per Trade Implementation - Status

**Date:** April 2, 2026  
**Status:** 🚧 IN PROGRESS  
**Completion:** 20%

---

## Completed ✅

### 1. Specification Document
- ✅ `PRO_RISK_MANAGEMENT_SPEC.md` - Complete specification
- ✅ Formula documentation
- ✅ UI/UX design
- ✅ Risk levels defined

### 2. Database Migration
- ✅ `db/add_risk_per_trade.sql` - Migration script created
- ✅ Add `risk_per_trade` column to `autotrade_sessions`
- ✅ Default value: 2.00 (2%)
- ✅ Constraint: 0.5% - 10% range

### 3. Position Sizing Module
- ✅ `Bismillah/app/position_sizing.py` - Core calculation module
- ✅ `calculate_position_size()` function
- ✅ `format_risk_info()` helper
- ✅ `get_recommended_risk()` helper
- ✅ Input validation
- ✅ Error handling
- ✅ Logging

---

## Remaining Work 🚧

### 4. Supabase Repository Functions
**File:** `Bismillah/app/supabase_repo.py`

**Add functions:**
```python
def get_risk_per_trade(telegram_id: int) -> float:
    """Get user's risk per trade percentage"""
    
def set_risk_per_trade(telegram_id: int, risk_pct: float) -> dict:
    """Update user's risk per trade percentage"""
    
def get_user_balance(telegram_id: int, exchange_id: str) -> float:
    """Get user's current balance from exchange"""
```

### 5. AutoTrade Engine Integration
**File:** `Bismillah/app/autotrade_engine.py`

**Changes needed:**
- Import position_sizing module
- Remove fixed `amount` parameter from start_engine()
- Get `risk_per_trade` from database
- Get current balance from exchange
- Call `calculate_position_size()` before each trade
- Use calculated margin instead of fixed amount
- Update logging to show risk info

**Key changes:**
```python
# OLD
def start_engine(bot, user_id, api_key, api_secret, amount, leverage, ...):
    # Use fixed amount
    qty = calc_qty(symbol, amount * leverage, price)

# NEW
def start_engine(bot, user_id, api_key, api_secret, leverage, ...):
    # Get risk percentage
    risk_pct = get_risk_per_trade(user_id)
    
    # Get current balance
    balance = get_account_balance(client)
    
    # Calculate position size
    sizing = calculate_position_size(
        balance=balance,
        risk_pct=risk_pct,
        entry_price=signal['entry'],
        sl_price=signal['sl'],
        leverage=leverage,
        symbol=symbol
    )
    
    # Use calculated quantity
    qty = sizing['qty']
    margin = sizing['margin_required']
```

### 6. Handlers - Dashboard UI
**File:** `Bismillah/app/handlers_autotrade.py`

**Add callbacks:**
```python
async def at_risk_settings(update, context):
    """Show risk settings modal"""
    
async def at_set_risk_1(update, context):
    """Set risk to 1%"""
    
async def at_set_risk_2(update, context):
    """Set risk to 2%"""
    
async def at_set_risk_3(update, context):
    """Set risk to 3%"""
    
async def at_set_risk_5(update, context):
    """Set risk to 5%"""
```

**Update dashboard:**
- Add "Risk Settings" button
- Show current risk percentage
- Show calculated risk amount
- Show survivability info

### 7. Scalping Engine Integration
**File:** `Bismillah/app/scalping_engine.py`

**Changes needed:**
- Same as autotrade_engine.py
- Use position_sizing module
- Calculate position size dynamically

### 8. Registration Flow Update
**File:** `Bismillah/app/handlers_autotrade.py`

**Changes:**
- Remove "amount" input step
- Add "risk percentage" selection step
- Show risk level recommendations
- Explain compounding benefits

### 9. Testing
**File:** `test_risk_per_trade.py` (NEW)

**Tests needed:**
- Unit tests for position_sizing.py
- Integration tests for full flow
- Edge case testing
- Performance testing

### 10. Documentation
**Files:**
- User guide for risk management
- FAQ about risk percentages
- Examples and scenarios
- Migration guide for existing users

---

## Implementation Plan

### Phase 1: Core Functionality (Priority: HIGH)
**Estimated time:** 2-3 hours

1. ✅ Create position_sizing.py
2. ✅ Create database migration
3. ⏳ Add supabase_repo functions
4. ⏳ Update autotrade_engine.py
5. ⏳ Update scalping_engine.py

### Phase 2: UI/UX (Priority: HIGH)
**Estimated time:** 2-3 hours

6. ⏳ Add dashboard risk settings button
7. ⏳ Create risk settings modal
8. ⏳ Add risk selection callbacks
9. ⏳ Update registration flow
10. ⏳ Update dashboard display

### Phase 3: Testing & Deployment (Priority: MEDIUM)
**Estimated time:** 1-2 hours

11. ⏳ Write unit tests
12. ⏳ Write integration tests
13. ⏳ Test on staging
14. ⏳ Run database migration
15. ⏳ Deploy to production

### Phase 4: Documentation (Priority: LOW)
**Estimated time:** 1 hour

16. ⏳ Write user guide
17. ⏳ Create FAQ
18. ⏳ Document examples
19. ⏳ Migration guide

---

## Next Steps

### Immediate (Now):

1. **Add supabase_repo functions**
   - get_risk_per_trade()
   - set_risk_per_trade()
   - get_user_balance()

2. **Update autotrade_engine.py**
   - Import position_sizing
   - Remove fixed amount
   - Add dynamic calculation
   - Update logging

3. **Add dashboard UI**
   - Risk settings button
   - Risk selection modal
   - Callbacks

### After Core Complete:

4. **Testing**
   - Unit tests
   - Integration tests
   - Edge cases

5. **Deployment**
   - Run migration
   - Deploy code
   - Monitor

---

## Breaking Changes

### For Existing Users:

**Before:**
- User sets fixed margin (e.g., $10)
- Position size always same
- No compounding

**After:**
- User sets risk % (default 2%)
- Position size calculated dynamically
- Automatic compounding

**Migration:**
- All existing users get 2% default risk
- Can change in dashboard
- No action required

### For Registration:

**Before:**
```
Step 1: Enter API keys
Step 2: Enter margin amount ($)
Step 3: Select leverage
Step 4: Start trading
```

**After:**
```
Step 1: Enter API keys
Step 2: Select risk percentage (%)
Step 3: Select leverage
Step 4: Start trading
```

---

## Risks & Mitigation

### Risk 1: Calculation Errors
**Impact:** Wrong position size → Wrong risk
**Mitigation:** 
- Extensive unit tests
- Input validation
- Error handling
- Logging

### Risk 2: Balance Fetch Failures
**Impact:** Can't calculate position size
**Mitigation:**
- Retry logic
- Fallback to last known balance
- Error notifications

### Risk 3: User Confusion
**Impact:** Users don't understand new system
**Mitigation:**
- Clear UI/UX
- Tooltips and help text
- Examples and scenarios
- Support documentation

### Risk 4: Migration Issues
**Impact:** Existing users affected
**Mitigation:**
- Safe default (2%)
- Backward compatibility
- Gradual rollout
- Monitoring

---

## Success Metrics

### Week 1:
- [ ] 0 critical bugs
- [ ] 50%+ users understand new system
- [ ] No account blow-ups
- [ ] Positive feedback

### Month 1:
- [ ] 80%+ users using risk per trade
- [ ] Average account growth: +10%
- [ ] User retention: +20%
- [ ] Support tickets: <5% increase

### Quarter 1:
- [ ] 95%+ adoption
- [ ] Average account growth: +30%
- [ ] Platform volume: +50%
- [ ] User satisfaction: 90%+

---

## Estimated Total Time

**Development:** 6-8 hours
**Testing:** 2-3 hours
**Deployment:** 1-2 hours
**Documentation:** 1 hour

**Total:** 10-14 hours

---

## Current Status Summary

✅ **Completed:** 20%
- Specification done
- Database migration ready
- Position sizing module complete

🚧 **In Progress:** 0%
- Nothing currently in progress

⏳ **Remaining:** 80%
- Supabase functions
- Engine integration
- UI/UX
- Testing
- Deployment

---

**Next Action:** Continue implementation with supabase_repo functions

**Estimated completion:** 10-14 hours of focused work

**Priority:** HIGH - This is a game-changing feature!

---

**Status By:** Kiro AI  
**Date:** April 2, 2026  
**Last Updated:** Just now
