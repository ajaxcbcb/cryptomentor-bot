# Risk Slider Implementation Plan — Fixed Dollar Risk Per Trade

## Context

Current state: Risk-based position sizing already exists in the backend (via `risk_per_trade` in autotrade_sessions), but users have no UI to adjust it.

User requirement: **High-frequency trading with fixed dollar risk** — allow users to set risk per trade (0.25%, 0.5%, 0.75%, 1%) via a web dashboard slider.

**Key Concept**: Dollar risk stays constant, position size scales inversely with SL distance
- Entry at support with tight SL (2%) → Larger position (say 0.5 BTC)
- Entry at resistance with wide SL (5%) → Smaller position (say 0.2 BTC)
- **Both trades risk the same $100** if user sets 1% risk on $10k account

This enables high-frequency small-risk trades → low individual risk, high win frequency acceptable, high potential reward.

---

## Problem Statement

1. **No risk control UI** — Users can't adjust `risk_per_trade` from web dashboard
2. **Default is 2%** — Hardcoded fallback, not user-adjustable
3. **No feedback** — Users don't see how their risk setting affects position sizing
4. **Signal algorithm doesn't adapt** — Fixed TP distances regardless of risk tolerance

---

## Proposed Solution

### 1. Backend: Risk Settings API
- New `GET /dashboard/settings` → Returns current risk_per_trade
- New `PUT /dashboard/settings/risk` → Saves new risk_per_trade (0.25, 0.5, 0.75, 1.0)
- Modify signal execution to use current risk setting from autotrade_sessions
- Optional: Scale TP targets based on risk tolerance (aggressive users = wider TPs)

### 2. Frontend: Risk Slider in Engine Tab
- Add "Risk Management" card to EngineTab
- Slider or buttons for: 0.25%, 0.5%, 0.75%, 1%
- Show preview: "Your account ($10k) will risk $100 per trade at 1%"
- Save immediately to backend
- Visual feedback: color scale (green=safe, orange=moderate, red=aggressive)

### 3. Signal Algorithm Adaptation (Optional)
- **Conservative (0.25%)** — Smaller position sizes, tighter TPs (0.5× ATR), skip borderline signals
- **Moderate (0.5-0.75%)** — Standard ATR scaling (0.75–1.5× ATR per tier)
- **Aggressive (1%)** — Larger position sizes, wider TPs (1.5–2.0× ATR), accept lower-confidence signals (score ≥ 45 instead of 50)

This allows different trader profiles:
- **Risk-averse**: 0.25% = many small wins, low leverage
- **Balanced**: 0.5% = standard confluent setups
- **Aggressive**: 1% = higher frequency, wider targets, accept more trades

---

## Implementation

### Phase 1: Backend Settings Endpoints

**File**: `website-backend/app/routes/dashboard.py`

**New Functions**:
```python
@router.get("/settings")
async def get_settings(tg_id: int = Depends(get_current_user)):
    """Get current trading settings (risk_per_trade, leverage, etc.)"""
    s = _client()
    res = s.table("autotrade_sessions").select(
        "risk_per_trade, leverage, trading_mode, risk_mode"
    ).eq("telegram_id", tg_id).limit(1).execute()
    
    sess = (res.data or [{}])[0]
    return {
        "risk_per_trade": float(sess.get("risk_per_trade") or 0.5),
        "leverage": int(sess.get("leverage") or 10),
        "trading_mode": sess.get("trading_mode") or "auto",
        "risk_mode": sess.get("risk_mode") or "moderate",
    }

@router.put("/settings/risk")
async def update_risk_setting(
    payload: dict,
    tg_id: int = Depends(get_current_user)
):
    """Update risk_per_trade for user (0.25, 0.5, 0.75, 1.0)"""
    risk = float(payload.get("risk_per_trade") or 0.5)
    
    # Validate: only allow 0.25, 0.5, 0.75, 1.0
    valid_risks = [0.25, 0.5, 0.75, 1.0]
    if risk not in valid_risks:
        raise HTTPException(400, f"Invalid risk: {risk}. Must be one of {valid_risks}")
    
    s = _client()
    s.table("autotrade_sessions").update({
        "risk_per_trade": risk,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("telegram_id", tg_id).execute()
    
    return {"success": True, "risk_per_trade": risk}
```

### Phase 2: Frontend Risk Slider

**File**: `website-frontend/src/App.jsx`

**In EngineTab** component, add a new card:
```jsx
<div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-amber-500/30 
    rounded-[1.5rem] md:rounded-[2.5rem] p-6 md:p-8 relative overflow-hidden">
  <h3 className="text-xl md:text-2xl font-black text-white mb-4">Risk Management</h3>
  <p className="text-slate-400 text-xs md:text-sm mb-6">
    Set your fixed dollar risk per trade. Position sizes automatically scale with stop loss distance.
  </p>
  
  {/* Risk Level Buttons */}
  <div className="grid grid-cols-4 gap-3 mb-6">
    {[0.25, 0.5, 0.75, 1.0].map(risk => (
      <button
        key={risk}
        onClick={() => updateRiskSetting(risk)}
        className={`py-3 px-2 rounded-lg font-bold text-xs transition-all ${
          currentRisk === risk
            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
            : 'bg-[#050505] text-slate-400 border border-white/5 hover:border-white/10'
        }`}
      >
        {risk}%
      </button>
    ))}
  </div>
  
  {/* Preview Calculation */}
  {accountBalance && (
    <div className="bg-[#050505]/50 border border-white/5 p-4 rounded-lg">
      <p className="text-[10px] text-slate-500 font-bold uppercase mb-2">Risk Preview</p>
      <p className="text-sm text-slate-300">
        Your account <span className="text-cyan-400 font-bold">${accountBalance.toLocaleString()}</span> will risk 
        <span className="text-amber-400 font-bold"> ${(accountBalance * currentRisk / 100).toLocaleString()}</span> per trade
      </p>
    </div>
  )}
  
  {/* Risk Gauge */}
  <div className="mt-4 p-3 bg-[#050505] rounded-lg border border-white/5">
    <div className="flex justify-between items-center mb-2">
      <span className="text-[10px] font-bold text-slate-500">Risk Level</span>
      <span className="text-xs font-bold text-amber-400">{currentRisk}%</span>
    </div>
    <div className="w-full h-2 bg-[#0a0a0a] rounded-full overflow-hidden border border-white/5">
      <div 
        className={`h-full transition-all ${
          currentRisk <= 0.25 ? 'bg-green-500' : 
          currentRisk <= 0.5 ? 'bg-cyan-500' : 
          currentRisk <= 0.75 ? 'bg-yellow-500' : 'bg-orange-500'
        }`}
        style={{width: `${(currentRisk / 1.0) * 100}%`}}
      />
    </div>
  </div>
</div>
```

### Phase 3: Update Signal Execution

**File**: `website-backend/app/routes/signals.py`

Modify `execute_signal()` to ensure it reads current `risk_per_trade` from autotrade_sessions:
```python
# Already exists, just ensure it's using latest:
sess_res = s.table("autotrade_sessions").select(
    "risk_per_trade, leverage"
).eq("telegram_id", tg_id).limit(1).execute()
sess = (sess_res.data or [{}])[0]
risk_pct = float(sess.get("risk_per_trade") or 0.5)  # No longer defaults to 2.0
```

### Phase 4: Optional — Signal Algorithm Adaptation

**File**: `website-backend/app/routes/signals.py`

Modify `generate_confluence_signals()` to adapt based on user risk preference:

```python
async def generate_confluence_signals(
    symbol: str, 
    user_risk_pct: float = 0.5  # Read from session
) -> Optional[Dict[str, Any]]:
    # ...existing confluence scoring...
    
    # Adapt confidence threshold based on risk tolerance
    min_confidence = {
        0.25: 60,  # Conservative: only high-confidence signals
        0.5: 50,   # Balanced: standard
        0.75: 45,  # Aggressive: accept borderline
        1.0: 40,   # Very aggressive: more signals
    }.get(user_risk_pct, 50)
    
    if score < min_confidence:
        return None  # Only generate if score meets risk-adjusted threshold
    
    # Scale TPs based on risk tolerance
    atr_multiplier = {
        0.25: 0.5,   # Tighter TPs
        0.5: 1.0,    # Standard
        0.75: 1.25,  # Wider TPs
        1.0: 1.5,    # Very wide TPs
    }.get(user_risk_pct, 1.0)
    
    tp1 = entry + (atr * 0.75 * atr_multiplier)
    tp2 = entry + (atr * 1.25 * atr_multiplier)
    tp3 = entry + (atr * 1.5 * atr_multiplier)
    
    # ...rest of signal generation...
```

---

## Files to Modify

| File | Change | Reason |
|------|--------|--------|
| `website-backend/app/routes/dashboard.py` | Add `GET /settings` and `PUT /settings/risk` | Backend risk API |
| `website-frontend/src/App.jsx` | Add Risk Management card to EngineTab | Frontend slider control |
| `website-backend/app/routes/signals.py` | Remove hardcoded 2.0 default, use session value; optional: adapt confidence threshold & TP scaling | Use current user risk |

---

## Verification

### 1. API Testing
```bash
# Get current risk
curl -H "Authorization: Bearer {token}" https://api/dashboard/settings

# Update risk
curl -X PUT -H "Authorization: Bearer {token}" \
  -d '{"risk_per_trade": 1.0}' \
  https://api/dashboard/settings/risk
```

### 2. UI Testing
- Load EngineTab
- Click risk level button (0.25%, 0.5%, 0.75%, 1%)
- Verify preview calculation: "Account $10k will risk $100 at 1%"
- Refresh page → risk setting persists from DB

### 3. Position Sizing Testing
- Set risk to 1%, account balance $10k
- Generate signal with SL distance 2% → expect position size ~500 coins
- Generate signal with SL distance 5% → expect position size ~200 coins
- Verify both trade the same dollar amount ($100)

### 4. Signal Generation Testing (if implementing Phase 4)
- Set risk to 0.25% (conservative)
- Observe only high-confidence signals (score ≥ 60)
- Set risk to 1% (aggressive)
- Observe more signals (score ≥ 40), wider TPs

---

## Success Criteria

✅ Users can adjust risk from 0.25% to 1%
✅ Risk setting persists across sessions
✅ Position sizing formula: `qty = (balance × risk%) / SL_distance`
✅ Preview shows actual dollar risk
✅ Signal execution reads user's current risk setting
✅ Optional: Signal generation adapts confidence threshold & TP scaling
✅ UI integrates seamlessly into EngineTab design language

---

## Timeline

- Phase 1 (Backend API): 15 min
- Phase 2 (Frontend UI): 20 min
- Phase 3 (Signal integration): 5 min
- Phase 4 (Optional adaptation): 15 min
- Testing: 15 min
- **Total: ~70 min (without Phase 4 optional feature)**

---

## Notes

1. **No Leverage Adjustment**: Risk slider only affects dollar risk per trade, not leverage. Users can still adjust leverage separately in Settings.

2. **Position Sizing**: Already implemented in `execute_signal` endpoint. This change just ensures the risk value is user-adjustable.

3. **Multiple Signals Per Day**: With aggressive risk (1%), users will see more signals due to lower confidence threshold, enabling high-frequency trading.

4. **Backward Compat**: Default 0.5% (middle ground) maintains existing behavior for users who don't set preference.
