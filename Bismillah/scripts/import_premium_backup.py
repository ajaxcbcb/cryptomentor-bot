
#!/usr/bin/env python3
"""
Import Premium Users from JSON Backup to Supabase
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.supabase_conn import supabase_upsert_user
from app.db_router import get_user

def import_premium_backup():
    """Import premium users from JSON backup to Supabase"""
    backup_file = "premium_users_backup_20250802_130229.json"
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    try:
        # Load backup data
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        premium_users = backup_data.get('premium_users', [])
        total_users = len(premium_users)
        
        print(f"📊 Found {total_users} premium users to import")
        print(f"📅 Backup date: {backup_data.get('backup_timestamp', 'Unknown')}")
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, user_data in enumerate(premium_users, 1):
            telegram_id = user_data.get('telegram_id')
            first_name = user_data.get('first_name', 'Unknown')
            username = user_data.get('username', 'no_username')
            
            print(f"[{i}/{total_users}] Processing {first_name} (@{username}) - ID: {telegram_id}")
            
            try:
                # Check if user exists
                existing_user = get_user(telegram_id)
                
                # Prepare user data for upsert
                user_payload = {
                    'telegram_id': telegram_id,
                    'first_name': user_data.get('first_name'),
                    'last_name': None,  # Not in backup
                    'username': user_data.get('username'),
                    'language_code': 'id',  # Default
                    'is_premium': bool(user_data.get('is_premium', 0)),
                    'credits': 1000,  # Give premium credits
                    'subscription_end': user_data.get('subscription_end'),
                    'created_at': user_data.get('created_at')
                }
                
                # Upsert user to Supabase
                result = supabase_upsert_user(telegram_id, user_payload)
                
                if result.get('success'):
                    if existing_user:
                        updated_count += 1
                        print(f"  ✅ Updated existing user")
                    else:
                        imported_count += 1
                        print(f"  ✅ Imported new user")
                else:
                    error_count += 1
                    print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                error_count += 1
                print(f"  ❌ Error processing user: {str(e)}")
        
        # Final summary
        print("\n" + "="*50)
        print("📊 IMPORT SUMMARY")
        print("="*50)
        print(f"✅ New imports: {imported_count}")
        print(f"🔄 Updates: {updated_count}")
        print(f"⏭️ Skipped: {skipped_count}")
        print(f"❌ Errors: {error_count}")
        print(f"📊 Total processed: {imported_count + updated_count + skipped_count + error_count}/{total_users}")
        
        success_rate = ((imported_count + updated_count) / total_users) * 100 if total_users > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting premium users import from JSON backup...")
    success = import_premium_backup()
    
    if success:
        print("\n✅ Import completed successfully!")
    else:
        print("\n❌ Import completed with errors!")
        sys.exit(1)
