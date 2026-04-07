-- Add Risk Per Trade column to autotrade_sessions
-- Professional money management: User selects risk % instead of fixed margin

-- Add risk_per_trade column (default 2% - moderate risk)
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS risk_per_trade DECIMAL(5,2) DEFAULT 2.00;

-- Set default for existing users (2% - recommended for most traders)
UPDATE autotrade_sessions 
SET risk_per_trade = 2.00 
WHERE risk_per_trade IS NULL;

-- Add constraint: risk must be between 0.5% and 10%
-- This prevents users from setting dangerously high risk
-- Drop constraint if exists (for re-running migration)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'risk_per_trade_range'
    ) THEN
        ALTER TABLE autotrade_sessions DROP CONSTRAINT risk_per_trade_range;
    END IF;
END $$;

-- Add the constraint
ALTER TABLE autotrade_sessions 
ADD CONSTRAINT risk_per_trade_range 
CHECK (risk_per_trade >= 0.5 AND risk_per_trade <= 10.0);

-- Add comment for documentation
COMMENT ON COLUMN autotrade_sessions.risk_per_trade IS 'Risk percentage per trade (e.g., 2.00 = 2%). Used for automatic position sizing based on account balance and stop loss distance.';
