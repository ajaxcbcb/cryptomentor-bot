
#!/usr/bin/env python3
"""
Setup Supabase tables for CryptoMentor AI Bot
"""

import os
from supabase_client import supabase
from datetime import datetime

def create_users_table():
    """Create users table in Supabase with proper structure"""
    try:
        print("🔧 Creating users table in Supabase...")
        
        # SQL to create users table with all required columns
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            language_code TEXT DEFAULT 'id',
            is_premium BOOLEAN DEFAULT FALSE,
            credits INTEGER DEFAULT 100,
            subscription_end TIMESTAMPTZ,
            referred_by BIGINT,
            referral_code TEXT,
            premium_referral_code TEXT,
            premium_earnings INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
        CREATE INDEX IF NOT EXISTS idx_users_premium_referral_code ON users(premium_referral_code);
        CREATE INDEX IF NOT EXISTS idx_users_is_premium ON users(is_premium);
        """
        
        # Execute SQL using Supabase RPC
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        if result.data:
            print("✅ Users table created successfully")
            return True
        else:
            print("❌ Failed to create users table")
            return False
            
    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        return False

def create_subscriptions_table():
    """Create subscriptions table"""
    try:
        print("🔧 Creating subscriptions table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            plan TEXT,
            status TEXT,
            start_date TIMESTAMPTZ DEFAULT NOW(),
            end_date TIMESTAMPTZ,
            granted_by BIGINT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_subscriptions_telegram_id ON subscriptions(telegram_id);
        """
        
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        if result.data:
            print("✅ Subscriptions table created successfully")
            return True
        else:
            print("❌ Failed to create subscriptions table")
            return False
            
    except Exception as e:
        print(f"❌ Error creating subscriptions table: {e}")
        return False

def create_portfolio_table():
    """Create portfolio table"""
    try:
        print("🔧 Creating portfolio table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS portfolio (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            symbol TEXT NOT NULL,
            amount DECIMAL NOT NULL,
            avg_buy_price DECIMAL NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_portfolio_telegram_id ON portfolio(telegram_id);
        """
        
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        if result.data:
            print("✅ Portfolio table created successfully")
            return True
        else:
            print("❌ Failed to create portfolio table")
            return False
            
    except Exception as e:
        print(f"❌ Error creating portfolio table: {e}")
        return False

def create_user_activity_table():
    """Create user_activity table"""
    try:
        print("🔧 Creating user_activity table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_activity (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);
        """
        
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        if result.data:
            print("✅ User activity table created successfully")
            return True
        else:
            print("❌ Failed to create user activity table")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user activity table: {e}")
        return False

def create_premium_referrals_table():
    """Create premium_referrals table"""
    try:
        print("🔧 Creating premium_referrals table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS premium_referrals (
            id BIGSERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT NOT NULL,
            subscription_type TEXT,
            subscription_amount INTEGER,
            earnings INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            paid_at TIMESTAMPTZ,
            FOREIGN KEY (referrer_id) REFERENCES users(telegram_id),
            FOREIGN KEY (referred_id) REFERENCES users(telegram_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_premium_referrals_referrer ON premium_referrals(referrer_id);
        CREATE INDEX IF NOT EXISTS idx_premium_referrals_referred ON premium_referrals(referred_id);
        """
        
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        if result.data:
            print("✅ Premium referrals table created successfully")
            return True
        else:
            print("❌ Failed to create premium referrals table")
            return False
            
    except Exception as e:
        print(f"❌ Error creating premium referrals table: {e}")
        return False

def test_connection_and_tables():
    """Test connection and verify tables exist"""
    try:
        print("🔍 Testing Supabase connection and tables...")
        
        # Test basic connection
        result = supabase.table('users').select('count', count='exact').limit(1).execute()
        print(f"✅ Connection test successful - Users table accessible")
        
        # Test other tables
        tables_to_test = ['subscriptions', 'portfolio', 'user_activity', 'premium_referrals']
        
        for table in tables_to_test:
            try:
                result = supabase.table(table).select('count', count='exact').limit(1).execute()
                print(f"✅ {table} table accessible")
            except Exception as e:
                print(f"❌ {table} table error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def setup_all_tables():
    """Setup all required tables"""
    print("🚀 Setting up Supabase database for CryptoMentor AI...")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = <REDACTED_SUPABASE_KEY>
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        print("Please add them to Replit Secrets")
        return False
    
    print(f"🔗 Supabase URL: {supabase_url}")
    print(f"🔑 API Key: {supabase_key[:20]}...")
    
    success = True
    
    # Create tables in order (respecting foreign key dependencies)
    tables_created = 0
    
    if create_users_table():
        tables_created += 1
    else:
        success = False
    
    if create_subscriptions_table():
        tables_created += 1
    else:
        success = False
    
    if create_portfolio_table():
        tables_created += 1
    else:
        success = False
    
    if create_user_activity_table():
        tables_created += 1
    else:
        success = False
    
    if create_premium_referrals_table():
        tables_created += 1
    else:
        success = False
    
    print("=" * 50)
    
    if success:
        print(f"✅ Database setup completed! {tables_created}/5 tables created")
        
        # Test the setup
        if test_connection_and_tables():
            print("✅ All tables are accessible and ready for use")
            return True
        else:
            print("⚠️ Tables created but some accessibility issues detected")
            return False
    else:
        print("❌ Database setup failed")
        return False

if __name__ == "__main__":
    setup_all_tables()
