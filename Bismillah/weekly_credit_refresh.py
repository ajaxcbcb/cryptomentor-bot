
#!/usr/bin/env python3
"""
Weekly Credit Refresh System for CryptoMentor AI
Gives 100 free credits to all non-premium users every week
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database

class WeeklyCreditRefresh:
    def __init__(self):
        load_dotenv()
        self.db = Database()
        
    def refresh_credits_for_free_users(self):
        """Give 100 credits to all non-premium users"""
        print("🔄 Starting weekly credit refresh...")
        print("=" * 50)
        
        try:
            # Get all non-premium users
            self.db.cursor.execute("""
                SELECT telegram_id, first_name, username, credits, is_premium
                FROM users 
                WHERE (is_premium = 0 OR is_premium IS NULL) 
                AND telegram_id IS NOT NULL 
                AND telegram_id != 0
            """)
            
            free_users = self.db.cursor.fetchall()
            total_free_users = len(free_users)
            
            if total_free_users == 0:
                print("ℹ️ No free users found in database")
                return
                
            print(f"👥 Found {total_free_users} free users")
            
            # Update credits for all free users
            updated_count = 0
            total_credits_given = 0
            
            for user in free_users:
                telegram_id, first_name, username, current_credits, is_premium = user
                
                # Set credits to 100 for free users
                new_credits = 100
                
                try:
                    self.db.cursor.execute("""
                        UPDATE users SET credits = ? WHERE telegram_id = ?
                    """, (new_credits, telegram_id))
                    
                    # Log the credit refresh
                    self.db.cursor.execute("""
                        INSERT INTO user_activity (telegram_id, action, details)
                        VALUES (?, ?, ?)
                    """, (telegram_id, "weekly_credit_refresh", f"Credits refreshed to {new_credits} (was {current_credits})"))
                    
                    updated_count += 1
                    total_credits_given += new_credits
                    
                    print(f"✅ {first_name} (@{username or 'no_username'}): {current_credits} → {new_credits} credits")
                    
                except Exception as e:
                    print(f"❌ Error updating user {telegram_id}: {e}")
                    continue
            
            # Commit all changes
            self.db.conn.commit()
            
            # Final statistics
            print("\n" + "=" * 50)
            print("✅ WEEKLY CREDIT REFRESH COMPLETED!")
            print(f"📊 Users updated: {updated_count}/{total_free_users}")
            print(f"💰 Total credits distributed: {total_credits_given:,}")
            print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
            
            # Log admin activity
            admin_id = int(os.getenv('ADMIN_USER_ID', '0'))
            if admin_id > 0:
                self.db.cursor.execute("""
                    INSERT INTO user_activity (telegram_id, action, details)
                    VALUES (?, ?, ?)
                """, (admin_id, "system_credit_refresh", f"Weekly refresh: {updated_count} users got 100 credits each"))
                self.db.conn.commit()
            
            return {
                'success': True,
                'users_updated': updated_count,
                'total_users': total_free_users,
                'credits_given': total_credits_given
            }
            
        except Exception as e:
            print(f"❌ Critical error during credit refresh: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.db.close()
    
    def get_refresh_statistics(self):
        """Get statistics about the last credit refresh"""
        try:
            # Get total free users
            self.db.cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE (is_premium = 0 OR is_premium IS NULL) 
                AND telegram_id IS NOT NULL
            """)
            total_free_users = self.db.cursor.fetchone()[0]
            
            # Get last refresh activity
            self.db.cursor.execute("""
                SELECT COUNT(*), MAX(timestamp) FROM user_activity 
                WHERE action = 'weekly_credit_refresh'
                AND timestamp >= datetime('now', '-7 days')
            """)
            last_refresh_data = self.db.cursor.fetchone()
            recent_refreshes = last_refresh_data[0] if last_refresh_data[0] else 0
            last_refresh_time = last_refresh_data[1] if last_refresh_data[1] else "Never"
            
            # Get users with 100 credits (recently refreshed)
            self.db.cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE credits = 100 
                AND (is_premium = 0 OR is_premium IS NULL)
                AND telegram_id IS NOT NULL
            """)
            users_with_100_credits = self.db.cursor.fetchone()[0]
            
            return {
                'total_free_users': total_free_users,
                'recent_refreshes': recent_refreshes,
                'last_refresh_time': last_refresh_time,
                'users_with_100_credits': users_with_100_credits
            }
            
        except Exception as e:
            print(f"Error getting refresh statistics: {e}")
            return None
        finally:
            self.db.close()

def main():
    """Main function for scheduled execution"""
    print("🚀 CryptoMentor AI - Weekly Credit Refresh")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    
    refresh_system = WeeklyCreditRefresh()
    result = refresh_system.refresh_credits_for_free_users()
    
    if result['success']:
        print(f"\n🎉 SUCCESS: {result['users_updated']} users received 100 credits each!")
    else:
        print(f"\n❌ FAILED: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
