-- StackMentor System Migration
-- Add 3-tier TP tracking and breakeven mode support

-- Add TP price columns
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_price NUMERIC(18,8);

-- Add TP hit tracking
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_hit BOOLEAN DEFAULT FALSE;

-- Add TP hit timestamps
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_hit_at TIMESTAMPTZ;

-- Add breakeven mode flag
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS breakeven_mode BOOLEAN DEFAULT FALSE;

-- Add quantity splits for each TP
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp1 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp2 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp3 NUMERIC(18,8);

-- Add TP profit tracking
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS profit_tp1 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS profit_tp2 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS profit_tp3 NUMERIC(18,8);

-- Add strategy identifier
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS strategy TEXT DEFAULT 'stackmentor';

-- Create index for active StackMentor positions
CREATE INDEX IF NOT EXISTS idx_stackmentor_active 
ON autotrade_trades(telegram_id, status, breakeven_mode) 
WHERE status = 'open' AND strategy = 'stackmentor';

-- Create index for TP monitoring
CREATE INDEX IF NOT EXISTS idx_stackmentor_tp_monitor 
ON autotrade_trades(telegram_id, symbol, tp1_hit, tp2_hit, tp3_hit) 
WHERE status = 'open';

COMMENT ON COLUMN autotrade_trades.tp1_price IS 'StackMentor TP1: 50% at R:R 1:2';
COMMENT ON COLUMN autotrade_trades.tp2_price IS 'StackMentor TP2: 40% at R:R 1:3';
COMMENT ON COLUMN autotrade_trades.tp3_price IS 'StackMentor TP3: 10% at R:R 1:10';
COMMENT ON COLUMN autotrade_trades.breakeven_mode IS 'TRUE after TP1 hit, SL moved to entry';
COMMENT ON COLUMN autotrade_trades.strategy IS 'Trading strategy: stackmentor, premium, etc';
