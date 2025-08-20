CREATE OR REPLACE FUNCTION set_premium(
    p_telegram_id BIGINT,
    p_duration_type TEXT DEFAULT 'days',
    p_duration_value INTEGER DEFAULT 30
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    premium_until_date TIMESTAMPTZ;
    result JSON;
    current_user_row users%ROWTYPE;
BEGIN
    -- Calculate premium end date based on duration type
    IF p_duration_type = 'lifetime' THEN
        premium_until_date := NULL; -- NULL means lifetime
    ELSIF p_duration_type = 'days' THEN
        premium_until_date := NOW() + INTERVAL '1 day' * p_duration_value;
    ELSIF p_duration_type = 'months' THEN
        premium_until_date := NOW() + INTERVAL '1 month' * p_duration_value;
    ELSE
        RETURN json_build_object(
            'success', false,
            'error', 'Invalid duration_type. Use: days, months, or lifetime'
        );
    END IF;

    -- Check if user exists, if not create with basic info
    SELECT * INTO current_user_row FROM users WHERE telegram_id = p_telegram_id;

    IF NOT FOUND THEN
        -- Create new user with premium
        INSERT INTO users (
            telegram_id,
            first_name,
            username,
            credits,
            is_premium,
            is_lifetime,
            premium_until,
            created_at,
            updated_at
        ) VALUES (
            p_telegram_id,
            'User' || p_telegram_id::TEXT,
            NULL,
            100,
            true,
            (p_duration_type = 'lifetime'),
            premium_until_date,
            NOW(),
            NOW()
        );
    ELSE
        -- Update existing user
        UPDATE users SET
            is_premium = true,
            is_lifetime = (p_duration_type = 'lifetime'),
            premium_until = premium_until_date,
            updated_at = NOW()
        WHERE telegram_id = p_telegram_id;
    END IF;

    -- Build result with verification
    SELECT * INTO current_user_row FROM users WHERE telegram_id = p_telegram_id;

    result := json_build_object(
        'success', true,
        'telegram_id', p_telegram_id,
        'is_premium', current_user_row.is_premium,
        'is_lifetime', current_user_row.is_lifetime,
        'premium_until', current_user_row.premium_until,
        'duration_type', p_duration_type,
        'duration_value', p_duration_value,
        'verified_at', NOW()
    );

    RETURN result;

EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', SQLERRM,
            'telegram_id', p_telegram_id,
            'sql_state', SQLSTATE
        );
END;
$$;