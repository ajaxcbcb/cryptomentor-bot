
#!/usr/bin/env python3
"""Diagnostic tool untuk menganalisis masalah grant premium"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    sys.exit(1)

def diagnose_premium_issues():
    """Diagnose premium grant issues"""
    print("🔍 CryptoMentor AI - Premium Grant Diagnostics")
    print("=" * 60)
    
    load_dotenv()
    
    # Check admin configuration
    admin_id = os.getenv('ADMIN_USER_ID', '0')
    print(f"🔧 Admin ID from env: {admin_id}")
    
    if admin_id == '0':
        print("❌ ADMIN_USER_ID not set!")
        return False
    
    try:
        admin_id_int = int(admin_id)
        print(f"✅ Admin ID valid: {admin_id_int}")
    except ValueError:
        print(f"❌ Invalid admin ID format: {admin_id}")
        return False
    
    try:
        # Initialize database
        db = Database()
        print("✅ Database connection established")
        
        # Database health check
        print("\n📊 Database Health Check:")
        
        # Check tables exist
        required_tables = ['users', 'user_activity', 'subscriptions']
        for table in required_tables:
            try:
                db.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = db.cursor.fetchone()[0]
                print(f"✅ Table {table}: {count} records")
            except Exception as e:
                print(f"❌ Table {table}: Error - {e}")
        
        # Check for problematic users
        print("\n🔍 User Data Issues:")
        
        # Users with NULL telegram_id
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
        null_ids = db.cursor.fetchone()[0]
        print(f"❌ NULL/0 telegram_id users: {null_ids}")
        
        # Users with invalid data
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE first_name IS NULL OR first_name = ''")
        no_names = db.cursor.fetchone()[0]
        print(f"⚠️ Users without names: {no_names}")
        
        # Premium users check
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_count = db.cursor.fetchone()[0]
        print(f"⭐ Current premium users: {premium_count}")
        
        # Test premium functionality
        print("\n🧪 Testing Premium Functions:")
        
        # Test with a sample user ID
        test_user_id = 999999999  # Safe test ID
        
        # Test user creation
        print(f"Testing user creation for ID: {test_user_id}")
        create_success = db.create_user(
            telegram_id=test_user_id,
            username="test_premium_user",
            first_name="Test Premium",
            language_code='id'
        )
        print(f"User creation: {'✅ Success' if create_success else '❌ Failed'}")
        
        # Test premium grant
        if create_success:
            print("Testing premium grant...")
            premium_success = db.grant_premium(test_user_id, 30)
            print(f"Premium grant: {'✅ Success' if premium_success else '❌ Failed'}")
            
            # Verify premium status
            is_premium = db.is_user_premium(test_user_id)
            print(f"Premium verification: {'✅ Active' if is_premium else '❌ Inactive'}")
            
            # Clean up test user
            db.cursor.execute("DELETE FROM users WHERE telegram_id = ?", (test_user_id,))
            db.cursor.execute("DELETE FROM subscriptions WHERE telegram_id = ?", (test_user_id,))
            db.cursor.execute("DELETE FROM user_activity WHERE telegram_id = ?", (test_user_id,))
            db.conn.commit()
            print("🧹 Test user cleaned up")
        
        # Check for common issues
        print("\n🔧 Common Issues Check:")
        
        # Check for users with conflicting data
        db.cursor.execute("""
            SELECT telegram_id, first_name, username, is_premium, credits
            FROM users 
            WHERE telegram_id IS NOT NULL 
            AND (first_name IS NULL OR username IS NULL OR credits IS NULL)
            LIMIT 5
        """)
        problematic_users = db.cursor.fetchall()
        
        if problematic_users:
            print("⚠️ Users with incomplete data:")
            for user in problematic_users:
                print(f"   ID: {user[0]}, Name: {user[1]}, Username: {user[2]}, Premium: {user[3]}, Credits: {user[4]}")
        else:
            print("✅ No users with incomplete data found")
        
        # Database integrity check
        print("\n💾 Database Integrity:")
        try:
            db.cursor.execute("PRAGMA integrity_check")
            integrity = db.cursor.fetchone()[0]
            print(f"Database integrity: {'✅ OK' if integrity == 'ok' else '❌ Issues found'}")
        except Exception as e:
            print(f"❌ Integrity check failed: {e}")
        
        db.close()
        
        # Recommendations
        print("\n💡 Recommendations:")
        print("1. Always check if user exists before granting premium")
        print("2. Validate telegram_id format (must be positive integer)")
        print("3. Ensure user has used /start command first")
        print("4. Check admin permissions are correctly set")
        print("5. Monitor for Markdown parsing errors in messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_common_issues():
    """Fix common premium grant issues"""
    print("\n🔧 Fixing Common Issues:")
    
    try:
        db = Database()
        
        # Fix NULL telegram_id users
        db.cursor.execute("DELETE FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
        deleted_invalid = db.cursor.rowcount
        if deleted_invalid > 0:
            print(f"🗑️ Removed {deleted_invalid} users with invalid telegram_id")
        
        # Fix NULL credits
        db.cursor.execute("UPDATE users SET credits = 100 WHERE credits IS NULL")
        fixed_credits = db.cursor.rowcount
        if fixed_credits > 0:
            print(f"💰 Fixed credits for {fixed_credits} users")
        
        # Fix NULL names
        db.cursor.execute("UPDATE users SET first_name = 'Unknown' WHERE first_name IS NULL OR first_name = ''")
        fixed_names = db.cursor.rowcount
        if fixed_names > 0:
            print(f"👤 Fixed names for {fixed_names} users")
        
        # Fix NULL usernames
        db.cursor.execute("UPDATE users SET username = 'no_username' WHERE username IS NULL OR username = ''")
        fixed_usernames = db.cursor.rowcount
        if fixed_usernames > 0:
            print(f"📝 Fixed usernames for {fixed_usernames} users")
        
        db.conn.commit()
        db.close()
        
        print("✅ Common issues fixed!")
        
    except Exception as e:
        print(f"❌ Error fixing issues: {e}")

if __name__ == "__main__":
    success = diagnose_premium_issues()
    
    if success:
        print("\n" + "=" * 60)
        fix_choice = input("Fix common issues automatically? (y/n): ").lower().strip()
        if fix_choice == 'y':
            fix_common_issues()
    
    print("\n🎯 Next Steps:")
    print("1. Run this diagnostic before granting premium")
    print("2. Use /check_admin command to verify admin setup")
    print("3. Ensure users have used /start before granting premium")
    print("4. Check bot logs for specific error messages")
