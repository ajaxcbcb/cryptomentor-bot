-- One-click signal push + missed TP FOMO lifecycle tables
-- Includes risk_per_trade default policy update (3.0% for new/null-invalid rows).

-- 1) Risk default policy (default only; existing valid custom values unchanged)
ALTER TABLE IF EXISTS autotrade_sessions
  ALTER COLUMN risk_per_trade SET DEFAULT 3.0;

UPDATE autotrade_sessions
SET risk_per_trade = 3.0
WHERE risk_per_trade IS NULL
   OR risk_per_trade < 0.25
   OR risk_per_trade > 5.0;

-- 2) Canonical one-click signal events
CREATE TABLE IF NOT EXISTS one_click_signal_events (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  signal_id TEXT NOT NULL UNIQUE,
  signal_fingerprint TEXT NOT NULL,
  symbol TEXT NOT NULL,
  pair TEXT NOT NULL,
  signal_type TEXT NOT NULL DEFAULT 'Scalp',
  direction TEXT NOT NULL,
  confidence DECIMAL(10, 4) NOT NULL DEFAULT 0,
  gate_status TEXT NOT NULL DEFAULT 'approved',
  gate_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
  model_source TEXT NOT NULL DEFAULT 'canonical_pro_v1',
  quality_meta JSONB NOT NULL DEFAULT '{}'::jsonb,
  entry_price DECIMAL(20, 8) NOT NULL,
  sl_price DECIMAL(20, 8) NOT NULL,
  tp1_price DECIMAL(20, 8) NOT NULL,
  tp2_price DECIMAL(20, 8),
  tp3_price DECIMAL(20, 8),
  generated_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  outcome_deadline_at TIMESTAMPTZ NOT NULL,
  push_started_at TIMESTAMPTZ,
  push_completed_at TIMESTAMPTZ,
  outcome_status TEXT NOT NULL DEFAULT 'pending',
  outcome_level TEXT,
  outcome_price DECIMAL(20, 8),
  outcome_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS one_click_signal_events_fingerprint_idx
  ON one_click_signal_events (signal_fingerprint, generated_at DESC);

CREATE INDEX IF NOT EXISTS one_click_signal_events_outcome_idx
  ON one_click_signal_events (outcome_status, outcome_deadline_at);

CREATE INDEX IF NOT EXISTS one_click_signal_events_symbol_idx
  ON one_click_signal_events (symbol, generated_at DESC);

-- 3) Per-recipient push + missed-FOMO lifecycle
CREATE TABLE IF NOT EXISTS one_click_signal_receipts (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  signal_id TEXT NOT NULL REFERENCES one_click_signal_events(signal_id) ON DELETE CASCADE,
  telegram_id BIGINT NOT NULL,
  audience_status TEXT NOT NULL DEFAULT 'verified',
  eligible BOOLEAN NOT NULL DEFAULT TRUE,
  eligibility_reason TEXT,
  delivery_status TEXT NOT NULL DEFAULT 'pending',
  delivery_error TEXT,
  delivered_at TIMESTAMPTZ,
  opened_at TIMESTAMPTZ,
  opened_trade_id BIGINT,
  missed_alert_status TEXT NOT NULL DEFAULT 'pending',
  missed_alert_error TEXT,
  missed_alert_sent_at TIMESTAMPTZ,
  tp_level_hit TEXT,
  projected_pnl_usdt DECIMAL(20, 8),
  projected_rr DECIMAL(20, 8),
  risk_pct_used DECIMAL(10, 4),
  equity_used_usdt DECIMAL(20, 8),
  example_used BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (signal_id, telegram_id)
);

CREATE INDEX IF NOT EXISTS one_click_signal_receipts_delivery_idx
  ON one_click_signal_receipts (delivery_status, created_at DESC);

CREATE INDEX IF NOT EXISTS one_click_signal_receipts_missed_idx
  ON one_click_signal_receipts (missed_alert_status, delivered_at DESC);

CREATE INDEX IF NOT EXISTS one_click_signal_receipts_user_idx
  ON one_click_signal_receipts (telegram_id, created_at DESC);
