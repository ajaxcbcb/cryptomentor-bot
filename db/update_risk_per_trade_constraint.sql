-- Update risk_per_trade constraint to allow new values: 0.25, 0.5, 0.75, 1.0
-- Previous constraint was >= 0.5, but new risk management system supports 0.25%

-- Step 1: Drop old constraint
ALTER TABLE autotrade_sessions 
DROP CONSTRAINT IF EXISTS risk_per_trade_range;

-- Step 2: Add new constraint allowing 0.25% minimum
ALTER TABLE autotrade_sessions 
ADD CONSTRAINT risk_per_trade_range 
CHECK (risk_per_trade >= 0.25 AND risk_per_trade <= 10.0);

-- Step 3: Update default to 0.5 (moderate)
ALTER TABLE autotrade_sessions 
ALTER COLUMN risk_per_trade SET DEFAULT 0.50;

-- Step 4: Update comment
COMMENT ON COLUMN autotrade_sessions.risk_per_trade IS 
'Risk percentage per trade. Valid values: 0.25 (conservative), 0.5 (moderate), 0.75 (aggressive), 1.0 (very aggressive). Used for automatic position sizing.';
