
#!/usr/bin/env python3
from database import Database

def check_current_users():
    """Check current users in database"""
    print("🔍 Checking current users in CryptoMentor AI database...")
    print("=" * 50)
    
    try:
        # Initialize database
        db = Database()
        
        # Get comprehensive statistics
        stats = db.get_bot_statistics()
        
        print(f"👥 Total Users: {stats['total_users']}")
        print(f"⭐ Premium Users: {stats['premium_users']}")
        print(f"🆓 Free Users: {stats['total_users'] - stats['premium_users']}")
        print(f"📈 Active Today: {stats['active_today']}")
        print(f"💳 Total Credits: {stats['total_credits']}")
        print(f"📊 Average Credits/User: {stats['avg_credits']:.1f}")
        print(f"⚡ Commands Today: {stats['commands_today']}")
        print(f"📈 Total Analyses: {stats['analyses_count']}")
        
        # Get recent users
        print("\n👤 Recent Users:")
        db.cursor.execute("""
            SELECT telegram_id, first_name, username, credits, is_premium, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_users = db.cursor.fetchall()
        
        for user in recent_users:
            telegram_id, first_name, username, credits, is_premium, created_at = user
            premium_badge = "⭐" if is_premium else "🆓"
            print(f"  {premium_badge} {first_name} (@{username or 'no_username'}) - {credits} credits - {created_at}")
        
        # Check for data issues
        print("\n🔍 Data Quality Check:")
        
        # Users with 0 credits
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits = 0")
        zero_credits = db.cursor.fetchone()[0]
        
        # Users with NULL telegram_id
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL")
        null_ids = db.cursor.fetchone()[0]
        
        print(f"⚠️ Users with 0 credits: {zero_credits}")
        print(f"❌ Users with NULL telegram_id: {null_ids}")
        
        if zero_credits > 0:
            print("💡 Tip: Consider running credit distribution for 0-credit users")
        
        if null_ids > 0:
            print("🔧 Warning: Found users with NULL telegram_id - database needs cleanup")
        
        db.close()
        print("\n✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_current_users()
