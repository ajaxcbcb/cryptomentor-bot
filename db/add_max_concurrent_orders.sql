-- Add max_concurrent_orders column to autotrade_sessions
-- For risk-based mode: allows up to 4 concurrent orders with split margin

ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS max_concurrent_orders INT DEFAULT 1;

-- Update existing risk-based users to 4 orders
UPDATE autotrade_sessions 
SET max_concurrent_orders = 4 
WHERE risk_mode = 'risk_based';

-- Update existing manual users to 1 order (default)
UPDATE autotrade_sessions 
SET max_concurrent_orders = 1 
WHERE risk_mode = 'manual' OR risk_mode IS NULL;

-- Add comment
COMMENT ON COLUMN autotrade_sessions.max_concurrent_orders IS 'Maximum concurrent orders allowed. Risk-based: 4, Manual: 1';

-- Verify
SELECT telegram_id, risk_mode, max_concurrent_orders, initial_deposit, leverage 
FROM autotrade_sessions 
LIMIT 10;
