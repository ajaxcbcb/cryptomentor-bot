-- Signal Queue Table: Tracks signals across web & telegram systems
-- Ensures no duplicate execution and consistent queue ordering

CREATE TABLE IF NOT EXISTS signal_queue (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id BIGINT NOT NULL,
  symbol TEXT NOT NULL,
  direction TEXT NOT NULL,
  confidence DECIMAL(5, 2) NOT NULL,
  entry_price DECIMAL(20, 8) NOT NULL,
  tp1 DECIMAL(20, 8) NOT NULL,
  tp2 DECIMAL(20, 8) NOT NULL,
  tp3 DECIMAL(20, 8) NOT NULL,
  sl DECIMAL(20, 8) NOT NULL,
  generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  reason TEXT,
  source TEXT DEFAULT 'autotrade',
  status TEXT DEFAULT 'pending',
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS signal_queue_user_status_idx ON signal_queue(user_id, status, confidence DESC);
CREATE INDEX IF NOT EXISTS signal_queue_user_symbol_idx ON signal_queue(user_id, symbol);
