
#!/usr/bin/env python3
"""
Premium User Preservation Script
Ensures premium and lifetime users persist through deployments
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    sys.exit(1)

def backup_premium_users():
    """Backup all premium users to JSON"""
    try:
        db = Database()
        
        # Get all premium users
        db.cursor.execute("""
            SELECT telegram_id, first_name, last_name, username, language_code,
                   is_premium, credits, subscription_end, referral_code, 
                   premium_referral_code, premium_earnings, created_at
            FROM users 
            WHERE is_premium = 1
        """)
        
        premium_users = []
        for row in db.cursor.fetchall():
            user_data = {
                'telegram_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'username': row[3],
                'language_code': row[4],
                'is_premium': row[5],
                'credits': row[6],
                'subscription_end': row[7],
                'referral_code': row[8],
                'premium_referral_code': row[9],
                'premium_earnings': row[10],
                'created_at': row[11]
            }
            premium_users.append(user_data)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"premium_users_backup_{timestamp}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                'backup_date': timestamp,
                'total_premium_users': len(premium_users),
                'premium_users': premium_users
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Premium users backed up: {backup_file}")
        print(f"📊 Total premium users: {len(premium_users)}")
        
        # Also create a persistent backup
        with open("premium_users_persistent.json", 'w', encoding='utf-8') as f:
            json.dump({
                'backup_date': timestamp,
                'total_premium_users': len(premium_users),
                'premium_users': premium_users
            }, f, indent=2, ensure_ascii=False)
        
        db.close()
        return backup_file, len(premium_users)
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None, 0

def restore_premium_users(backup_file=None):
    """Restore premium users from backup"""
    try:
        # Use persistent backup if no specific file provided
        if backup_file is None:
            backup_file = "premium_users_persistent.json"
        
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        db = Database()
        restored_count = 0
        updated_count = 0
        
        for user_data in backup_data['premium_users']:
            telegram_id = user_data['telegram_id']
            
            # Check if user exists
            existing = db.get_user(telegram_id)
            if existing:
                # Update existing user to restore premium
                db.cursor.execute("""
                    UPDATE users 
                    SET is_premium = ?, credits = ?, subscription_end = ?,
                        referral_code = ?, premium_referral_code = ?, premium_earnings = ?
                    WHERE telegram_id = ?
                """, (
                    user_data['is_premium'],
                    max(user_data['credits'], existing['credits']),  # Keep higher credits
                    user_data['subscription_end'],
                    user_data['referral_code'],
                    user_data['premium_referral_code'],
                    user_data['premium_earnings'],
                    telegram_id
                ))
                updated_count += 1
                print(f"✅ Updated premium status for user {telegram_id}")
            else:
                # Restore missing user
                db.cursor.execute("""
                    INSERT INTO users 
                    (telegram_id, first_name, last_name, username, language_code, 
                     is_premium, credits, subscription_end, referral_code,
                     premium_referral_code, premium_earnings, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['telegram_id'],
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['username'],
                    user_data['language_code'],
                    user_data['is_premium'],
                    user_data['credits'],
                    user_data['subscription_end'],
                    user_data['referral_code'],
                    user_data['premium_referral_code'],
                    user_data['premium_earnings'],
                    user_data['created_at']
                ))
                restored_count += 1
                print(f"✅ Restored missing premium user {telegram_id}")
        
        db.conn.commit()
        
        # Verify restoration
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        total_premium = db.cursor.fetchone()[0]
        
        print(f"✅ Premium restoration completed!")
        print(f"📊 Restored: {restored_count} users")
        print(f"📊 Updated: {updated_count} users")
        print(f"📊 Total premium users now: {total_premium}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Restoration failed: {e}")
        return False

def auto_preserve_check():
    """Automatically check and preserve premium users on startup"""
    try:
        # Create backup before any operations
        backup_file, count = backup_premium_users()
        
        if count > 0:
            print(f"🔒 AUTO-PRESERVE: Backed up {count} premium users")
            
            # Verify they still exist in database
            db = Database()
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            current_count = db.cursor.fetchone()[0]
            
            if current_count < count:
                print(f"⚠️ PREMIUM LOSS DETECTED: {count} → {current_count}")
                print("🔄 Auto-restoring premium users...")
                restore_premium_users(backup_file)
            else:
                print(f"✅ Premium users intact: {current_count}")
            
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Auto-preserve failed: {e}")
        return False

if __name__ == "__main__":
    print("🔒 Premium User Preservation System")
    print("=" * 50)
    
    action = input("Choose action:\n1. Backup premium users\n2. Restore premium users\n3. Auto-check\nEnter (1/2/3): ").strip()
    
    if action == "1":
        backup_file, count = backup_premium_users()
        if backup_file:
            print(f"✅ Backup completed: {backup_file}")
    elif action == "2":
        success = restore_premium_users()
        if success:
            print("✅ Restoration completed!")
    elif action == "3":
        auto_preserve_check()
    else:
        print("❌ Invalid option")
