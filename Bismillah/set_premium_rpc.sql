
CREATE OR REPLACE FUNCTION set_premium(
  p_telegram_id BIGINT,
  p_duration_type TEXT,
  p_duration_value INTEGER DEFAULT 0
) 
RETURNS JSON AS $$
DECLARE
  premium_until_ts TIMESTAMPTZ;
  result_row users%ROWTYPE;
BEGIN
  -- Calculate premium_until based on duration type
  CASE p_duration_type
    WHEN 'lifetime' THEN
      premium_until_ts := NULL;
    WHEN 'days' THEN
      premium_until_ts := NOW() + (p_duration_value || ' days')::INTERVAL;
    WHEN 'months' THEN
      premium_until_ts := NOW() + (p_duration_value || ' months')::INTERVAL;
    ELSE
      RAISE EXCEPTION 'Invalid duration_type: %', p_duration_type;
  END CASE;

  -- Update user premium status
  UPDATE users 
  SET 
    is_premium = TRUE,
    is_lifetime = CASE WHEN p_duration_type = 'lifetime' THEN TRUE ELSE FALSE END,
    premium_until = premium_until_ts,
    updated_at = NOW()
  WHERE telegram_id = p_telegram_id
  RETURNING * INTO result_row;

  -- Check if user was found and updated
  IF NOT FOUND THEN
    RAISE EXCEPTION 'User with telegram_id % not found', p_telegram_id;
  END IF;

  -- Return success response
  RETURN json_build_object(
    'success', true,
    'telegram_id', result_row.telegram_id,
    'is_premium', result_row.is_premium,
    'is_lifetime', result_row.is_lifetime,
    'premium_until', result_row.premium_until
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
