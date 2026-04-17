-- One-Click Trades
-- First-class execution lifecycle for dashboard 1-click orders.

CREATE TABLE IF NOT EXISTS one_click_trades (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  telegram_id BIGINT NOT NULL,
  signal_id TEXT NOT NULL,
  client_request_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending_submit',
  entry_price DECIMAL(20, 8),
  sl_price DECIMAL(20, 8),
  tp_price DECIMAL(20, 8),
  qty DECIMAL(20, 8),
  leverage INTEGER,
  requested_risk_pct DECIMAL(10, 4),
  accepted_risk_pct DECIMAL(10, 4),
  risk_amount_usdt DECIMAL(20, 8),
  margin_required_usdt DECIMAL(20, 8),
  cap_applied BOOLEAN DEFAULT FALSE,
  cap_reason TEXT,
  exchange_order_id TEXT,
  exchange_position_id TEXT,
  reason_code TEXT,
  reason_message TEXT,
  opened_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS one_click_trades_req_uniq
  ON one_click_trades (telegram_id, client_request_id);

CREATE INDEX IF NOT EXISTS one_click_trades_symbol_status_idx
  ON one_click_trades (telegram_id, symbol, status, created_at DESC);

CREATE INDEX IF NOT EXISTS one_click_trades_open_idx
  ON one_click_trades (telegram_id, status, opened_at DESC);
