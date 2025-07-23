
#!/usr/bin/env python3
"""Check current users in CryptoMentor AI database"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    sys.exit(1)


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
        
        # Get premium users
        print("\n⭐ Premium Users:")
        db.cursor.execute("""
            SELECT telegram_id, first_name, username, subscription_end
            FROM users 
            WHERE is_premium = 1
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        premium_users = db.cursor.fetchall()
        
        if premium_users:
            for user in premium_users:
                telegram_id, first_name, username, sub_end = user
                sub_status = "Lifetime" if sub_end is None else f"Until {sub_end[:10]}"
                print(f"  💎 {first_name} (@{username or 'no_username'}) - {sub_status}")
        else:
            print("  No premium users found")
        
        # Check for data issues
        print("\n🔍 Data Quality Check:")
        
        # Users with 0 credits
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits = 0")
        zero_credits = db.cursor.fetchone()[0]
        
        # Users with NULL telegram_id
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL")
        null_ids = db.cursor.fetchone()[0]
        
        # Users with high credits (potential issues)
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits > 1000")
        high_credits = db.cursor.fetchone()[0]
        
        print(f"⚠️ Users with 0 credits: {zero_credits}")
        print(f"❌ Users with NULL telegram_id: {null_ids}")
        print(f"📈 Users with >1000 credits: {high_credits}")
        
        if zero_credits > 0:
            print("💡 Tip: Consider running credit distribution for 0-credit users")
        
        if null_ids > 0:
            print("🔧 Warning: Found users with NULL telegram_id - database needs cleanup")
        
        if high_credits > 0:
            print("📊 Info: Some users have very high credits - verify if intended")
        
        # Recent activity
        print("\n📊 Recent Activity (Last 24 hours):")
        db.cursor.execute("""
            SELECT action, COUNT(*) as count
            FROM user_activity 
            WHERE timestamp >= datetime('now', '-1 day')
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
        """)
        activities = db.cursor.fetchall()
        
        if activities:
            for action, count in activities:
                print(f"  • {action}: {count} times")
        else:
            print("  No recent activity recorded")
        
        db.close()
        print("\n✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    check_current_users()
