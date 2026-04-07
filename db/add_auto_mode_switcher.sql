-- Add auto_mode_enabled column to autotrade_sessions
-- This enables automatic mode switching based on market sentiment

ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS auto_mode_enabled BOOLEAN DEFAULT TRUE;

-- Add engine_active column to track if engine is running
ALTER TABLE autotrade_sessions
ADD COLUMN IF NOT EXISTS engine_active BOOLEAN DEFAULT FALSE;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_autotrade_auto_mode 
ON autotrade_sessions(auto_mode_enabled, engine_active);

-- Comment
COMMENT ON COLUMN autotrade_sessions.auto_mode_enabled IS 
'Enable automatic mode switching based on market sentiment (sideways → scalping, trending → swing)';

COMMENT ON COLUMN autotrade_sessions.engine_active IS
'Track if autotrade engine is currently running for this user';
