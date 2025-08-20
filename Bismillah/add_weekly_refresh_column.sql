
-- Add last_weekly_refresh column to users table if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_weekly_refresh TIMESTAMPTZ;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_users_last_weekly_refresh ON users(last_weekly_refresh);

-- Comment explaining the column
COMMENT ON COLUMN users.last_weekly_refresh IS 'Timestamp when user last received weekly credit refresh';
