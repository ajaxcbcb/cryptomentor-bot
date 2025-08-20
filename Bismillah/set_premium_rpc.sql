
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
      premium_until_ts := NOW() AT TIME ZONE 'UTC' + (p_duration_value || ' days')::INTERVAL;
    WHEN 'months' THEN
      premium_until_ts := NOW() AT TIME ZONE 'UTC' + (p_duration_value || ' months')::INTERVAL;
    ELSE
      RAISE EXCEPTION 'Invalid duration_type: %. Use lifetime, days, or months', p_duration_type;
  END CASE;

  -- Upsert user if not exists, then update premium status
  INSERT INTO users (telegram_id, is_premium, is_lifetime, premium_until, created_at, updated_at)
  VALUES (p_telegram_id, TRUE, (p_duration_type = 'lifetime'), premium_until_ts, NOW(), NOW())
  ON CONFLICT (telegram_id) 
  DO UPDATE SET 
    is_premium = TRUE,
    is_lifetime = (p_duration_type = 'lifetime'),
    premium_until = premium_until_ts,
    updated_at = NOW()
  RETURNING * INTO result_row;

  -- Return success response with user data
  RETURN json_build_object(
    'success', true,
    'telegram_id', result_row.telegram_id,
    'is_premium', result_row.is_premium,
    'is_lifetime', result_row.is_lifetime,
    'premium_until', result_row.premium_until,
    'updated_at', result_row.updated_at
  );
EXCEPTION
  WHEN OTHERS THEN
    RETURN json_build_object(
      'success', false,
      'error', SQLERRM,
      'telegram_id', p_telegram_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
