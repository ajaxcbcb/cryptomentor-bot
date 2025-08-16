
-- RPC function for safe user upsert
CREATE OR REPLACE FUNCTION upsert_user_rpc(
    p_telegram_id BIGINT,
    p_username TEXT DEFAULT NULL,
    p_first_name TEXT DEFAULT NULL,
    p_last_name TEXT DEFAULT NULL
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result_row users%ROWTYPE;
BEGIN
    -- Upsert user with only safe fields
    INSERT INTO users (telegram_id, username, first_name, last_name, created_at, updated_at)
    VALUES (p_telegram_id, p_username, p_first_name, p_last_name, NOW(), NOW())
    ON CONFLICT (telegram_id) 
    DO UPDATE SET 
        username = COALESCE(EXCLUDED.username, users.username),
        first_name = COALESCE(EXCLUDED.first_name, users.first_name),
        last_name = COALESCE(EXCLUDED.last_name, users.last_name),
        updated_at = NOW()
    RETURNING * INTO result_row;
    
    -- Return success with user data
    RETURN json_build_object(
        'success', true,
        'telegram_id', result_row.telegram_id,
        'username', result_row.username,
        'first_name', result_row.first_name,
        'is_premium', result_row.is_premium,
        'credits', result_row.credits
    );
    
EXCEPTION
    WHEN OTHERS THEN
        -- Return error details
        RETURN json_build_object(
            'success', false,
            'error', SQLERRM,
            'telegram_id', p_telegram_id
        );
END;
$$;

-- Grant execute permission to service role
GRANT EXECUTE ON FUNCTION upsert_user_rpc TO service_role;
GRANT EXECUTE ON FUNCTION upsert_user_rpc TO authenticated;
GRANT EXECUTE ON FUNCTION upsert_user_rpc TO anon;
