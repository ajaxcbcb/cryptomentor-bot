
#!/usr/bin/env python3
"""
Weekly Credit Refresh System for CryptoMentor AI (Supabase Version)
Gives 50 free credits to all non-premium users every Monday at midnight
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.supabase_conn import get_supabase_client
from app.users_repo import is_premium_active

class WeeklyCreditRefreshSupabase:
    def __init__(self):
        load_dotenv()
        
    def refresh_credits_for_free_users(self):
        """Give 50 credits to all non-premium users weekly"""
        print("🔄 Starting weekly Supabase credit refresh...")
        print("=" * 50)
        
        try:
            s = get_supabase_client()
            
            # Get all users with last refresh data
            result = s.table("users").select("telegram_id, first_name, username, credits, is_premium, is_lifetime, premium_until, last_weekly_refresh").execute()
            
            if not result.data:
                print("ℹ️ No users found in Supabase")
                return
                
            all_users = result.data
            free_users = []
            
            # Filter free users (non-premium)
            for user in all_users:
                tg_id = user.get('telegram_id')
                if not tg_id:
                    continue
                    
                # Check if user is premium
                if not is_premium_active(tg_id):
                    free_users.append(user)
            
            total_free_users = len(free_users)
            
            if total_free_users == 0:
                print("ℹ️ No free users found")
                return
                
            print(f"👥 Found {total_free_users} free users out of {len(all_users)} total users")
            
            # Update credits for all free users
            updated_count = 0
            total_credits_given = 0
            weekly_credit_amount = 100  # Changed from 50 to 100
            
            for user in free_users:
                telegram_id = user.get('telegram_id')
                first_name = user.get('first_name', 'Unknown')
                username = user.get('username', 'no_username')
                current_credits = user.get('credits', 0)
                
                # Set credits to 100 for free users (weekly refresh)
                new_credits = weekly_credit_amount
                
                try:
                    # Check if user was already refreshed this week
                    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
                    last_refresh = user.get('last_weekly_refresh')
                    
                    if last_refresh and last_refresh > week_ago:
                        print(f"⏭️ {first_name} (@{username}): Already refreshed this week, skipping")
                        continue
                    
                    # Update user credits and mark refresh time
                    now = datetime.utcnow().isoformat()
                    update_result = s.table("users").update({
                        "credits": new_credits,
                        "last_weekly_refresh": now
                    }).eq("telegram_id", telegram_id).execute()
                    
                    if update_result.data:
                        updated_count += 1
                        total_credits_given += new_credits
                        
                        print(f"✅ {first_name} (@{username}): {current_credits} → {new_credits} credits")
                    else:
                        print(f"❌ Failed to update user {telegram_id}")
                    
                except Exception as e:
                    print(f"❌ Error updating user {telegram_id}: {e}")
                    continue
            
            # Calculate next refresh date
            from datetime import datetime, timedelta
            now = datetime.now()
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 0:  # If it's Monday but past midnight
                days_until_monday = 7
            next_refresh = now + timedelta(days=days_until_monday)
            next_refresh = next_refresh.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Format next refresh with date and day
            next_refresh_str = next_refresh.strftime('%A, %d %B %Y - 00:00 WIB')
            
            # Final statistics
            print("\n" + "=" * 50)
            print("✅ WEEKLY CREDIT REFRESH COMPLETED!")
            print(f"📊 Users updated: {updated_count}/{total_free_users}")
            print(f"💰 Total credits distributed: {total_credits_given:,} (100 credits per user)")
            print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
            print(f"📅 Next refresh: {next_refresh_str}")
            
            return {
                'success': True,
                'users_updated': updated_count,
                'total_users': total_free_users,
                'credits_given': total_credits_given
            }
            
        except Exception as e:
            print(f"❌ Critical error during Supabase credit refresh: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_refresh_statistics(self):
        """Get statistics about the last credit refresh"""
        try:
            s = get_supabase_client()
            
            # Get total free users
            result = s.table("users").select("telegram_id, is_premium, is_lifetime, premium_until").execute()
            
            free_users_count = 0
            total_users = len(result.data) if result.data else 0
            
            for user in result.data or []:
                tg_id = user.get('telegram_id')
                if tg_id and not is_premium_active(tg_id):
                    free_users_count += 1
            
            # Get users with recent refresh
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            recent_refresh_result = s.table("users").select("telegram_id, last_weekly_refresh").gte("last_weekly_refresh", week_ago).execute()
            
            recent_refreshes = len(recent_refresh_result.data) if recent_refresh_result.data else 0
            
            # Get last refresh time
            last_refresh_result = s.table("users").select("last_weekly_refresh").order("last_weekly_refresh", desc=True).limit(1).execute()
            last_refresh_time = "Never"
            if last_refresh_result.data:
                last_refresh_time = last_refresh_result.data[0].get("last_weekly_refresh", "Never")
            
            return {
                'total_users': total_users,
                'total_free_users': free_users_count,
                'recent_refreshes': recent_refreshes,
                'last_refresh_time': last_refresh_time
            }
            
        except Exception as e:
            print(f"Error getting refresh statistics: {e}")
            return None

def main():
    """Main function for scheduled execution"""
    print("🚀 CryptoMentor AI - Weekly Credit Refresh (Supabase)")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    
    # Check if it's Sunday night/Monday morning (Sunday = 6, Monday = 0)
    current_day = datetime.now().weekday()
    current_hour = datetime.now().hour
    
    print(f"📅 Current day: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]}")
    print(f"🕐 Current hour: {current_hour}")
    
    refresh_system = WeeklyCreditRefreshSupabase()
    
    # Force run if argument provided, or if it's Monday at midnight (00:00-01:00)
    force_run = len(sys.argv) > 1 and sys.argv[1] == "--force"
    
    # Run on Monday between 00:00-01:00 (start of week) to account for timing
    is_monday_refresh_time = current_day == 0 and current_hour == 0
    
    if force_run or is_monday_refresh_time:
        result = refresh_system.refresh_credits_for_free_users()
        
        if result['success']:
            print(f"\n🎉 SUCCESS: {result['users_updated']} users received 50 credits each!")
        else:
            print(f"\n❌ FAILED: {result['error']}")
            sys.exit(1)
    else:
        print("ℹ️ Not Monday midnight - refresh skipped")
        print("💡 Use --force to run anyway")
        
        # Show statistics
        stats = refresh_system.get_refresh_statistics()
        if stats:
            print(f"\n📊 Current Statistics:")
            print(f"• Total users: {stats['total_users']}")
            print(f"• Free users: {stats['total_free_users']}")
            print(f"• Recent refreshes: {stats['recent_refreshes']}")
            print(f"• Last refresh: {stats['last_refresh_time']}")

if __name__ == "__main__":
    main()
