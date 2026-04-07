-- TP Partial & SL BEP Tracking
-- Add columns to track multiple TP levels and SL BEP status

-- Add new columns to autotrade_trades table
ALTER TABLE autotrade_trades 
ADD COLUMN IF NOT EXISTS position_id TEXT,
ADD COLUMN IF NOT EXISTS original_quantity NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS remaining_quantity NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp1_price NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp2_price NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp3_price NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp1_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp2_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp3_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp1_hit_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS tp2_hit_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS tp3_hit_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS sl_moved_to_bep BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS sl_bep_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS tp1_quantity NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp2_quantity NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp3_quantity NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp1_profit NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp2_profit NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS tp3_profit NUMERIC(18,8);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_autotrade_trades_position_id ON autotrade_trades(position_id);
CREATE INDEX IF NOT EXISTS idx_autotrade_trades_tp_status ON autotrade_trades(tp1_hit, tp2_hit, tp3_hit) WHERE status = 'open';

-- Add comment for documentation
COMMENT ON COLUMN autotrade_trades.position_id IS 'Bitunix position ID for TP/SL modification';
COMMENT ON COLUMN autotrade_trades.original_quantity IS 'Original position quantity at entry';
COMMENT ON COLUMN autotrade_trades.remaining_quantity IS 'Remaining quantity after partial closes';
COMMENT ON COLUMN autotrade_trades.tp1_price IS 'TP1 price (1:2 R:R) - 60% close';
COMMENT ON COLUMN autotrade_trades.tp2_price IS 'TP2 price (1:3 R:R) - 30% close';
COMMENT ON COLUMN autotrade_trades.tp3_price IS 'TP3 price (1:5 R:R) - 10% close';
COMMENT ON COLUMN autotrade_trades.tp1_quantity IS 'Quantity closed at TP1 (60%)';
COMMENT ON COLUMN autotrade_trades.tp2_quantity IS 'Quantity closed at TP2 (30%)';
COMMENT ON COLUMN autotrade_trades.tp3_quantity IS 'Quantity closed at TP3 (10%)';
COMMENT ON COLUMN autotrade_trades.sl_moved_to_bep IS 'Whether SL has been moved to breakeven after TP1';
