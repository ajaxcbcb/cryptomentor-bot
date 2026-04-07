-- ============================================================
-- Migration: Add Trading Mode Support
-- Description: Add trading_mode column to autotrade_sessions
-- Date: 2024
-- ============================================================

-- Add trading_mode column
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(20) DEFAULT 'swing';

-- Add comment for documentation
COMMENT ON COLUMN autotrade_sessions.trading_mode IS 
'Trading mode: scalping (5M high-frequency) or swing (15M multi-tier)';

-- Create index for faster mode queries
CREATE INDEX IF NOT EXISTS idx_autotrade_sessions_trading_mode 
ON autotrade_sessions(telegram_id, trading_mode);

-- Update existing rows to default swing mode
UPDATE autotrade_sessions 
SET trading_mode = 'swing' 
WHERE trading_mode IS NULL;

-- Add constraint to ensure valid values
ALTER TABLE autotrade_sessions
ADD CONSTRAINT chk_trading_mode 
CHECK (trading_mode IN ('scalping', 'swing'));

-- ============================================================
-- Verification Queries
-- ============================================================

-- Check column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'autotrade_sessions'
  AND column_name = 'trading_mode';

-- Check index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'autotrade_sessions'
  AND indexname = 'idx_autotrade_sessions_trading_mode';

-- Check data distribution
SELECT trading_mode, COUNT(*) as user_count
FROM autotrade_sessions
GROUP BY trading_mode;

-- ============================================================
-- Rollback Script (if needed)
-- ============================================================

-- DROP CONSTRAINT IF EXISTS chk_trading_mode;
-- DROP INDEX IF EXISTS idx_autotrade_sessions_trading_mode;
-- ALTER TABLE autotrade_sessions DROP COLUMN IF EXISTS trading_mode;
