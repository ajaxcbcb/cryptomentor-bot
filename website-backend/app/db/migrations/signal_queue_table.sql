-- Signal Queue Table: Tracks signals across web & telegram systems
-- Ensures no duplicate execution and consistent queue ordering

CREATE TABLE IF NOT EXISTS signal_queue (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id BIGINT NOT NULL,
  symbol TEXT NOT NULL,
  direction TEXT NOT NULL, -- LONG or SHORT
  confidence DECIMAL(5, 2) NOT NULL,
  entry_price DECIMAL(20, 8) NOT NULL,
  tp1 DECIMAL(20, 8) NOT NULL,
  tp2 DECIMAL(20, 8) NOT NULL,
  tp3 DECIMAL(20, 8) NOT NULL,
  sl DECIMAL(20, 8) NOT NULL,
  generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  reason TEXT,
  source TEXT DEFAULT 'autotrade', -- 'autotrade' or 'web'
  status TEXT DEFAULT 'pending', -- pending, executing, executed, failed
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Constraints
  CONSTRAINT user_symbol_unique UNIQUE(user_id, symbol, status) WHERE status IN ('pending', 'executing')
);

-- Index for fast queue retrieval
CREATE INDEX IF NOT EXISTS signal_queue_user_status_idx ON signal_queue(user_id, status, confidence DESC);
CREATE INDEX IF NOT EXISTS signal_queue_user_symbol_idx ON signal_queue(user_id, symbol);

-- Enable RLS
ALTER TABLE signal_queue ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own signals
CREATE POLICY "Users can view own signals"
  ON signal_queue FOR SELECT
  USING (auth.uid()::TEXT::BIGINT = user_id OR user_id = (SELECT telegram_id FROM auth.users WHERE auth.users.id = auth.uid()));

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_signal_queue_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER signal_queue_update_timestamp
BEFORE UPDATE ON signal_queue
FOR EACH ROW
EXECUTE FUNCTION update_signal_queue_timestamp();
