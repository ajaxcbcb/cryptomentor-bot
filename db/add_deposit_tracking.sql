-- Add deposit tracking for StackMentor eligibility
-- Users with total_deposit >= 60 USDT can use StackMentor

-- Add total_deposit column
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_deposit NUMERIC(18,2) DEFAULT 0.00;

-- Add index for StackMentor eligibility check
CREATE INDEX IF NOT EXISTS idx_users_deposit ON users(total_deposit) WHERE total_deposit >= 60;

-- Comment
COMMENT ON COLUMN users.total_deposit IS 'Total lifetime deposits in USDT - determines StackMentor eligibility (>= $60)';

-- Function to update deposit
CREATE OR REPLACE FUNCTION public.add_user_deposit(
  p_telegram_id BIGINT,
  p_amount NUMERIC
) RETURNS NUMERIC LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_new_total NUMERIC;
BEGIN
  UPDATE public.users
  SET total_deposit = COALESCE(total_deposit, 0) + p_amount
  WHERE telegram_id = p_telegram_id
  RETURNING total_deposit INTO v_new_total;

  -- Log event
  INSERT INTO public.user_events (telegram_id, event_type, meta)
  VALUES (p_telegram_id, 'ADD_DEPOSIT', jsonb_build_object('amount', p_amount, 'new_total', v_new_total));

  RETURN v_new_total;
END$$;

-- Function to check StackMentor eligibility
CREATE OR REPLACE FUNCTION public.is_stackmentor_eligible(p_telegram_id BIGINT)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
  SELECT COALESCE(total_deposit, 0) >= 60
  FROM public.users
  WHERE telegram_id = p_telegram_id;
$$;
