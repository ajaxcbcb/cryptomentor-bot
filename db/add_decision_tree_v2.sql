-- Decision Tree V2 candidate logging and trade metadata

CREATE TABLE IF NOT EXISTS public.trade_candidates_log (
  id bigserial PRIMARY KEY,
  decision_trace_id text NOT NULL,
  cycle_id text,
  user_id bigint NOT NULL REFERENCES public.users(telegram_id) ON DELETE CASCADE,
  symbol text NOT NULL,
  engine text NOT NULL,
  side text NOT NULL,
  regime text,
  setup_name text,
  quality_bucket text,
  participation_bucket text,
  expected_hold_profile text,
  expected_user_friendliness text,
  expected_volume_contribution_class text,
  user_equity_tier text,
  signal_confidence numeric(8,4),
  tradeability_score numeric(8,4),
  approval_score numeric(8,4),
  community_score numeric(8,4),
  user_segment_score numeric(8,4),
  portfolio_penalty numeric(8,4),
  final_score numeric(8,4),
  recommended_risk_pct numeric(8,4),
  approved boolean NOT NULL DEFAULT false,
  reject_reason text,
  display_reason text,
  approval_audit jsonb DEFAULT '{}'::jsonb,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trade_candidates_log_user_created
ON public.trade_candidates_log(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_trade_candidates_log_trace
ON public.trade_candidates_log(decision_trace_id);

ALTER TABLE public.trade_candidates_log ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'trade_candidates_log' AND policyname = 'trade_candidates_log_service_only'
  ) THEN
    EXECUTE 'CREATE POLICY trade_candidates_log_service_only ON public.trade_candidates_log FOR ALL USING (true) WITH CHECK (true)';
  END IF;
END $$;

ALTER TABLE public.autotrade_trades
ADD COLUMN IF NOT EXISTS decision_trace_id text,
ADD COLUMN IF NOT EXISTS decision_mode_version text,
ADD COLUMN IF NOT EXISTS decision_regime text,
ADD COLUMN IF NOT EXISTS decision_final_score numeric(8,4),
ADD COLUMN IF NOT EXISTS decision_quality_score numeric(8,4),
ADD COLUMN IF NOT EXISTS decision_community_score numeric(8,4),
ADD COLUMN IF NOT EXISTS decision_user_segment_score numeric(8,4);

