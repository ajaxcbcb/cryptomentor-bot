-- Migration: add_sideways_scalping_fields
-- Adds sideways micro-scalping metadata fields to autotrade_trades table

ALTER TABLE public.autotrade_trades
  ADD COLUMN IF NOT EXISTS trade_type               text,
  ADD COLUMN IF NOT EXISTS trade_subtype            text,
  ADD COLUMN IF NOT EXISTS timeframe                text,
  ADD COLUMN IF NOT EXISTS tp_strategy              text,
  ADD COLUMN IF NOT EXISTS max_hold_time            integer,
  ADD COLUMN IF NOT EXISTS close_reason             text,
  ADD COLUMN IF NOT EXISTS close_price              numeric(18,8),
  ADD COLUMN IF NOT EXISTS quantity                 numeric(18,8),
  ADD COLUMN IF NOT EXISTS range_support            numeric(18,8),
  ADD COLUMN IF NOT EXISTS range_resistance         numeric(18,8),
  ADD COLUMN IF NOT EXISTS range_width_pct          numeric(6,4),
  ADD COLUMN IF NOT EXISTS bounce_confirmed         boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS rsi_divergence_detected  boolean DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_autotrade_trades_subtype
  ON public.autotrade_trades(trade_subtype)
  WHERE trade_subtype IS NOT NULL;
