# System Audit Plan - CryptoMentor Bot

## Audit Scope

### 1. User Registration & Onboarding Flow
- `/start` command handler
- User registration (Supabase + SQLite)
- Referral system
- Welcome credits
- Initial setup flow

### 2. AutoTrade Flow
- `/autotrade` command
- Exchange selection
- API key setup
- UID verification (Bitunix)
- Risk mode selection
- Trading mode selection
- Engine startup

### 3. Menu Handlers
- Dashboard callbacks
- Settings menu
- Trading mode switch
- Risk mode switch
- Position management
- Trade history
- Skills menu
- Community partners

### 4. Engine Operations
- Auto-restore on bot restart
- Health check system
- Position monitoring
- Signal generation
- Order execution
- Partial TP handling

### 5. Error Handling
- API errors
- Database errors
- Exchange errors
- User notifications

## Audit Process

1. Read all handler files
2. Check for:
   - Missing error handling
   - Broken callbacks
   - Race conditions
   - Database inconsistencies
   - Missing validations
   - UX issues
3. Document findings
4. Propose fixes
5. Implement critical fixes

## Files to Audit

### Core Handlers
- `Bismillah/bot.py` - Main entry point
- `Bismillah/app/handlers_autotrade.py` - AutoTrade flow
- `Bismillah/app/handlers_risk_mode.py` - Risk management
- `Bismillah/app/trading_mode_manager.py` - Trading mode
- `Bismillah/app/handlers_community.py` - Community features
- `Bismillah/app/handlers_skills.py` - Skills system

### Engine Files
- `Bismillah/app/autotrade_engine.py` - Swing engine
- `Bismillah/app/scalping_engine.py` - Scalping engine
- `Bismillah/app/scheduler.py` - Auto-restore & health check

### Support Files
- `Bismillah/app/supabase_repo.py` - Database operations
- `Bismillah/app/exchange_registry.py` - Exchange configs
- `Bismillah/app/error_handler.py` - Error handling

## Expected Issues to Look For

1. **Registration Issues**
   - Duplicate user handling
   - Referral code validation
   - Credit allocation

2. **AutoTrade Issues**
   - API key validation
   - Exchange compatibility
   - UID verification flow
   - Risk mode setup

3. **Menu Issues**
   - Broken callbacks
   - Missing handlers
   - Inconsistent state

4. **Engine Issues**
   - Race conditions
   - Memory leaks
   - Error recovery

5. **UX Issues**
   - Confusing messages
   - Missing feedback
   - Unclear flows

## Audit Timeline

- Phase 1: Registration & Onboarding (30 min)
- Phase 2: AutoTrade Flow (45 min)
- Phase 3: Menu Handlers (30 min)
- Phase 4: Engine Operations (30 min)
- Phase 5: Error Handling (15 min)
- Phase 6: Fix Implementation (60 min)

Total: ~3.5 hours

## Output

- Detailed audit report with findings
- Prioritized fix list
- Implementation of critical fixes
- Deployment plan
