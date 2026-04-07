-- Add risk_mode column to autotrade_sessions
-- Date: April 2, 2026
-- Feature: Dual Mode Risk Management (Recommended vs Manual)

-- Add column
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS risk_mode VARCHAR(20) DEFAULT 'risk_based';

-- Set existing users to 'manual' mode for backward compatibility
UPDATE autotrade_sessions 
SET risk_mode = 'manual' 
WHERE risk_mode IS NULL OR risk_mode = '';

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_autotrade_sessions_risk_mode 
ON autotrade_sessions(risk_mode);

-- Add comment
COMMENT ON COLUMN autotrade_sessions.risk_mode IS 
'Risk management mode: risk_based (recommended, auto-calculate from balance) or manual (user sets margin)';

-- Verify
SELECT 
    telegram_id,
    risk_mode,
    risk_per_trade,
    initial_deposit,
    leverage
FROM autotrade_sessions
LIMIT 5;
