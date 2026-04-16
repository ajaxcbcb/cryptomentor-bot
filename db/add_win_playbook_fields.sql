-- Win Playbook + Runtime Risk Overlay fields
-- Durable win-reason tracking + execution metadata on autotrade_trades

ALTER TABLE public.autotrade_trades
ADD COLUMN IF NOT EXISTS win_reasoning TEXT,
ADD COLUMN IF NOT EXISTS win_reason_tags JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS playbook_match_score NUMERIC(6,3),
ADD COLUMN IF NOT EXISTS effective_risk_pct NUMERIC(6,3),
ADD COLUMN IF NOT EXISTS risk_overlay_pct NUMERIC(6,3);

CREATE INDEX IF NOT EXISTS idx_autotrade_trades_playbook_match
ON public.autotrade_trades(playbook_match_score);

COMMENT ON COLUMN public.autotrade_trades.win_reasoning IS 'Structured reasoning for why a profitable trade won.';
COMMENT ON COLUMN public.autotrade_trades.win_reason_tags IS 'Matched playbook tags associated with winning close.';
COMMENT ON COLUMN public.autotrade_trades.playbook_match_score IS 'Playbook match score snapshot at execution/close.';
COMMENT ON COLUMN public.autotrade_trades.effective_risk_pct IS 'Runtime effective risk used for sizing (base risk + overlay, capped).';
COMMENT ON COLUMN public.autotrade_trades.risk_overlay_pct IS 'Runtime-only global risk overlay applied on top of base risk.';
