import sqlite3
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="cryptomentor.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Check if tables exist and add missing columns if needed
        try:
            # Create users table with all required columns
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    language_code TEXT DEFAULT 'id',
                    is_premium INTEGER DEFAULT 0,
                    credits INTEGER DEFAULT 0,
                    subscription_end TEXT,
                    referred_by INTEGER,
                    referral_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Check if telegram_id column exists, if not add it
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]

            if 'telegram_id' not in columns:
                print("Adding missing telegram_id column to users table...")
                self.cursor.execute("ALTER TABLE users ADD COLUMN telegram_id INTEGER")

            if 'language_code' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN language_code TEXT DEFAULT 'id'")

            if 'is_premium' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")

            if 'credits' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0")

            if 'subscription_end' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN subscription_end TEXT")

            if 'referred_by' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")

            if 'referral_code' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")

        except Exception as e:
            print(f"Error updating users table schema: {e}")
            # If there's an error, drop and recreate the table
            self.cursor.execute("DROP TABLE IF EXISTS users")
            self.cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    language_code TEXT DEFAULT 'id',
                    is_premium INTEGER DEFAULT 0,
                    credits INTEGER DEFAULT 0,
                    subscription_end TEXT,
                    referred_by INTEGER,
                    referral_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Create subscriptions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                plan TEXT,
                status TEXT,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                granted_by INTEGER
            )
        """)

        # Create portfolio table
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    symbol TEXT,
                    amount REAL,
                    avg_buy_price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            """)

            # Check if telegram_id column exists in portfolio
            self.cursor.execute("PRAGMA table_info(portfolio)")
            portfolio_columns = [column[1] for column in self.cursor.fetchall()]
            if 'telegram_id' not in portfolio_columns:
                print("Adding missing telegram_id column to portfolio table...")
                self.cursor.execute("ALTER TABLE portfolio ADD COLUMN telegram_id INTEGER")

        except Exception as e:
            print(f"Error with portfolio table: {e}")

        # Create user activity log table
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            """)

            # Check if telegram_id column exists in user_activity
            self.cursor.execute("PRAGMA table_info(user_activity)")
            activity_columns = [column[1] for column in self.cursor.fetchall()]
            if 'telegram_id' not in activity_columns:
                print("Adding missing telegram_id column to user_activity table...")
                self.cursor.execute("ALTER TABLE user_activity ADD COLUMN telegram_id INTEGER")

        except Exception as e:
            print(f"Error with user_activity table: {e}")

        self.conn.commit()

    def create_user(self, telegram_id, username, first_name=None, last_name=None, language_code='id', referred_by=None):
        """Create a new user in the database"""
        try:
            # Check if user already exists
            existing_user = self.get_user(telegram_id)
            if existing_user:
                print(f"User {telegram_id} already exists")
                return True

            # Generate unique referral code
            import random
            import string
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # Base credits: 10 for all users
            base_credits = 10

            # Bonus credits: +5 if referred
            bonus_credits = 5 if referred_by else 0
            total_credits = base_credits + bonus_credits

            # Insert new user
            self.cursor.execute("""
                INSERT INTO users 
                (telegram_id, first_name, last_name, username, language_code, credits, referral_code, referred_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (telegram_id, first_name, last_name, username, language_code, total_credits, referral_code, referred_by))
            self.conn.commit()

            # Log the user creation
            credit_msg = f"New user registered with {total_credits} credits ({base_credits} base"
            if referred_by:
                credit_msg += f" + {bonus_credits} referral bonus"
            credit_msg += ")"
            self.log_user_activity(telegram_id, "user_created", credit_msg)
            print(f"✅ New user {telegram_id} ({username}) created with {total_credits} credits")
            return True
        except Exception as e:
            print(f"DB Error (create_user): {e}")
            return False

    def add_user(self, telegram_id, first_name, last_name, username, language_code='id'):
        """Add a new user to the database"""
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO users 
                (telegram_id, first_name, last_name, username, language_code) 
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, first_name, last_name, username, language_code))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (add_user): {e}")
            return False

    def get_user(self, telegram_id):
        """Get user information by telegram_id"""
        try:
            self.cursor.execute("""
                SELECT telegram_id, first_name, last_name, username, language_code, 
                       is_premium, credits, subscription_end, referred_by, referral_code, created_at
                FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = self.cursor.fetchone()
            if row:
                return {
                    'telegram_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'username': row[3],
                    'language_code': row[4],
                    'is_premium': row[5],
                    'credits': row[6],
                    'subscription_end': row[7],
                    'referred_by': row[8],
                    'referral_code': row[9],
                    'created_at': row[10]
                }
            return None
        except Exception as e:
            print(f"DB Error (get_user): {e}")
            return None

    def update_user_language(self, telegram_id, language_code):
        """Update user's language preference"""
        try:
            self.cursor.execute("""
                UPDATE users SET language_code = ? WHERE telegram_id = ?
            """, (language_code, telegram_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (update_user_language): {e}")
            return False

    def is_user_premium(self, telegram_id):
        """Check if user has active premium subscription"""
        try:
            self.cursor.execute("""
                SELECT is_premium, subscription_end FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = self.cursor.fetchone()
            if row:
                is_premium, sub_end = row
                if is_premium:
                    # If subscription_end is NULL, it's permanent premium
                    if sub_end is None:
                        return True
                    else:
                        # Check if subscription is still valid
                        try:
                            end_date = datetime.fromisoformat(sub_end)
                            if datetime.now() > end_date:
                                # Subscription expired, update status
                                self.revoke_premium_access(telegram_id, None)
                                return False
                            return True
                        except ValueError:
                            # Invalid date format, treat as permanent premium
                            print(f"Invalid subscription_end format for user {telegram_id}, treating as permanent")
                            return True
                return False
            return False
        except Exception as e:
            print(f"DB Error (is_user_premium): {e}")
            return False

    def grant_premium_access(self, telegram_id, granted_by_id, days=30):
        """Grant premium access to a user"""
        try:
            # If days is None or 0, grant permanent premium
            if days is None or days == 0:
                end_date_str = None
                plan_type = 'permanent'
            else:
                end_date = datetime.now() + timedelta(days=days)
                end_date_str = end_date.isoformat()
                plan_type = 'premium'

            self.cursor.execute("""
                UPDATE users SET is_premium = 1, subscription_end = ? WHERE telegram_id = ?
            """, (end_date_str, telegram_id))

            # Log the subscription
            self.cursor.execute("""
                INSERT INTO subscriptions (telegram_id, plan, status, end_date, granted_by)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, plan_type, 'active', end_date_str, granted_by_id))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (grant_premium_access): {e}")
            return False

    def revoke_premium_access(self, telegram_id, revoked_by_id):
        """Revoke premium access from a user"""
        try:
            self.cursor.execute("""
                UPDATE users SET is_premium = 0, subscription_end = NULL WHERE telegram_id = ?
            """, (telegram_id,))

            # Update subscription status
            self.cursor.execute("""
                UPDATE subscriptions SET status = 'revoked' 
                WHERE telegram_id = ? AND status = 'active'
            """, (telegram_id,))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (revoke_premium_access): {e}")
            return False

    def get_user_portfolio(self, telegram_id):
        """Get user's portfolio"""
        try:
            self.cursor.execute("""
                SELECT symbol, amount, avg_buy_price, created_at 
                FROM portfolio WHERE telegram_id = ?
            """, (telegram_id,))
            rows = self.cursor.fetchall()
            return [{'symbol': row[0], 'amount': row[1], 'avg_buy_price': row[2], 'created_at': row[3]} for row in rows]
        except Exception as e:
            print(f"DB Error (get_user_portfolio): {e}")
            return []

    def add_portfolio_item(self, telegram_id, symbol, amount, avg_buy_price):
        """Add or update portfolio item"""
        try:
            # Check if item exists
            self.cursor.execute("""
                SELECT amount, avg_buy_price FROM portfolio 
                WHERE telegram_id = ? AND symbol = ?
            """, (telegram_id, symbol))
            existing = self.cursor.fetchone()

            if existing:
                # Update existing item (average the prices)
                old_amount, old_price = existing
                new_amount = old_amount + amount
                new_avg_price = ((old_amount * old_price) + (amount * avg_buy_price)) / new_amount

                self.cursor.execute("""
                    UPDATE portfolio SET amount = ?, avg_buy_price = ? 
                    WHERE telegram_id = ? AND symbol = ?
                """, (new_amount, new_avg_price, telegram_id, symbol))
            else:
                # Add new item
                self.cursor.execute("""
                    INSERT INTO portfolio (telegram_id, symbol, amount, avg_buy_price)
                    VALUES (?, ?, ?, ?)
                """, (telegram_id, symbol, amount, avg_buy_price))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (add_portfolio_item): {e}")
            return False

    def log_user_activity(self, telegram_id, action, details=""):
        """Log user activity"""
        try:
            self.cursor.execute("""
                INSERT INTO user_activity (telegram_id, action, details)
                VALUES (?, ?, ?)
            """, (telegram_id, action, details))
            self.conn.commit()
        except Exception as e:
            print(f"DB Error (log_user_activity): {e}")

    def get_user_stats(self):
        """Get user statistics for admin panel"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users")
            total_users = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            premium_users = self.cursor.fetchone()[0]

            free_users = total_users - premium_users

            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'free_users': free_users
            }
        except Exception as e:
            print(f"DB Error (get_user_stats): {e}")
            return {'total_users': 0, 'premium_users': 0, 'free_users': 0}

    def get_user_credits(self, telegram_id):
        """Get user's remaining credits"""
        try:
            self.cursor.execute("""
                SELECT credits FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = self.cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            print(f"DB Error (get_user_credits): {e}")
            return 0

    def deduct_credit(self, telegram_id, amount):
        """Deduct credits from user (only for non-premium, non-admin users)"""
        try:
            # Check if user is admin or premium
            if self.is_user_premium(telegram_id) or telegram_id == int(os.getenv('ADMIN_USER_ID', '0')):
                # Admin and premium users don't lose credits
                return True

            self.cursor.execute("""
                UPDATE users SET credits = credits - ? 
                WHERE telegram_id = ? AND credits >= ?
            """, (amount, telegram_id, amount))

            if self.cursor.rowcount > 0:
                self.conn.commit()
                return True
            return False
        except Exception as e:
            print(f"DB Error (deduct_credit): {e}")
            return False

    def get_bot_stats(self):
        """Get bot statistics for admin panel"""
        try:
            # Total users
            self.cursor.execute("SELECT COUNT(*) FROM users")
            total_users = self.cursor.fetchone()[0]

            # Premium users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            premium_users = self.cursor.fetchone()[0]

            # Active today (users with activity in last 24 hours)
            self.cursor.execute("""
                SELECT COUNT(DISTINCT telegram_id) FROM user_activity 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            active_today = self.cursor.fetchone()[0]

            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'active_today': active_today
            }
        except Exception as e:
            print(f"DB Error (get_bot_stats): {e}")
            return {'total_users': 0, 'premium_users': 0, 'active_today': 0}

    def grant_premium(self, telegram_id, days=30):
        """Grant premium access to a user"""
        return self.grant_premium_access(telegram_id, None, days)

    def grant_permanent_premium(self, telegram_id):
        """Grant permanent premium access to a user"""
        return self.grant_premium_access(telegram_id, None, None)

    def revoke_premium(self, telegram_id):
        """Revoke premium access from a user"""
        return self.revoke_premium_access(telegram_id, None)

    def add_to_portfolio(self, telegram_id, symbol, amount, avg_buy_price=0):
        """Add coin to user's portfolio"""
        return self.add_portfolio_item(telegram_id, symbol, amount, avg_buy_price)

    def get_user_by_referral_code(self, referral_code):
        """Get user ID by referral code"""
        try:
            self.cursor.execute("""
                SELECT telegram_id FROM users WHERE referral_code = ?
            """, (referral_code,))
            row = self.cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            print(f"DB Error (get_user_by_referral_code): {e}")
            return

    def update_user_language(self, telegram_id, language):
        """Update user language preference"""
        try:
            self.cursor.execute("""
                UPDATE users SET language = ? WHERE telegram_id = ?
            """, (language, telegram_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (update_user_language): {e}")
            return False

    def get_bot_statistics(self):
        """Get bot usage statistics"""
        try:
            # Total users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
            total_users = self.cursor.fetchone()[0]

            # Premium users - fixed query
            self.cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE is_premium = 1 AND telegram_id IS NOT NULL
            """)
            premium_users = self.cursor.fetchone()[0]

            # Active today (users with activity in last 24 hours) - fixed column name
            self.cursor.execute("""
                SELECT COUNT(DISTINCT telegram_id) FROM user_activity 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            active_today = self.cursor.fetchone()[0]

            # Total credits 
            self.cursor.execute("SELECT COALESCE(SUM(credits), 0) FROM users WHERE telegram_id IS NOT NULL")
            total_credits = self.cursor.fetchone()[0]

            # Commands today
            self.cursor.execute("""
                SELECT COUNT(*) FROM user_activity 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            commands_today = self.cursor.fetchone()[0]

            # Average credits per user
            avg_credits = (total_credits / total_users) if total_users > 0 else 0

            # Total analyses count
            self.cursor.execute("""
                SELECT COUNT(*) FROM user_activity 
                WHERE action IN ('analyze', 'futures_analysis', 'market_overview')
            """)
            analyses_count = self.cursor.fetchone()[0]

            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'active_today': active_today,
                'total_credits': total_credits,
                'commands_today': commands_today,
                'avg_credits': avg_credits,
                'analyses_count': analyses_count
            }
        except Exception as e:
            print(f"DB Error (get_bot_statistics): {e}")
            return {
                'total_users': 0,
                'premium_users': 0,
                'active_today': 0,
                'total_credits': 0,
                'commands_today': 0,
                'avg_credits': 0,
                'analyses_count': 0
            }

    def get_recent_activity(self, limit=10):
        """Get recent user activity"""
        try:
            self.cursor.execute("""
                SELECT user_id, action, details, timestamp 
                FROM user_activity 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))

            activities = []
            for row in self.cursor.fetchall():
                activities.append({
                    'user_id': row[0],
                    'action': row[1],
                    'details': row[2],
                    'timestamp': row[3]
                })
            return activities
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []

    def get_all_users(self):
        """Get all users for broadcast functionality"""
        try:
            self.cursor.execute("""
                SELECT telegram_id, first_name, username, is_premium, created_at
                FROM users 
                WHERE telegram_id IS NOT NULL AND telegram_id != 0
                ORDER BY created_at DESC
            """)
            rows = self.cursor.fetchall()
            
            users = []
            for row in rows:
                users.append({
                    'user_id': row[0],
                    'first_name': row[1],
                    'username': row[2],
                    'is_premium': row[3],
                    'created_at': row[4]
                })
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []()

            users = []
            for row in rows:
                if row[0] and str(row[0]).isdigit():  # Validate telegram_id
                    users.append({
                        'user_id': int(row[0]),
                        'first_name': row[1] or 'Unknown',
                        'username': row[2] or 'No username',
                        'is_premium': row[3] or 0,
                        'created_at': row[4]
                    })

            print(f"📊 Retrieved {len(users)} valid users for broadcast")
            return users

        except Exception as e:
            print(f"DB Error (get_all_users): {e}")
            return []

    def add_credits(self, telegram_id, amount):
        """Add credits to user account"""
        try:
            # Check if user exists first
            user = self.get_user(telegram_id)
            if not user:
                print(f"User {telegram_id} not found for adding credits")
                return False

            self.cursor.execute("""
                UPDATE users SET credits = credits + ? WHERE telegram_id = ?
            """, (amount, telegram_id))
            
            if self.cursor.rowcount > 0:
                self.conn.commit()
                # Log the credit addition
                self.log_user_activity(telegram_id, "credits_added", f"Added {amount} credits by admin")
                print(f"✅ Added {amount} credits to user {telegram_id}")
                return True
            else:
                print(f"❌ Failed to add credits to user {telegram_id}")
                return False
        except Exception as e:
            print(f"DB Error (add_credits): {e}")
            return False

    def fix_user_credits(self):
        """Fix users with 0 or negative credits"""
        try:
            # Update users with 0 or negative credits to 10
            self.cursor.execute("""
                UPDATE users SET credits = 10 
                WHERE credits <= 0 AND telegram_id IS NOT NULL
            """)
            
            fixed_count = self.cursor.rowcount
            self.conn.commit()
            print(f"✅ Fixed credits for {fixed_count} users")
            return fixed_count
        except Exception as e:
            print(f"DB Error (fix_user_credits): {e}")
            return 0

    def set_user_language(self, telegram_id, language):
        """Set user's language preference"""
        try:
            self.cursor.execute("""
                UPDATE users SET language_code = ? WHERE telegram_id = ?
            """, (language, telegram_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"DB Error (set_user_language): {e}")
            return False

    def mark_all_users_for_restart(self):
        """Mark all users to require /start again (for admin restart)"""
        try:
            # Add restart_required column if it doesn't exist
            try:
                self.cursor.execute("ALTER TABLE users ADD COLUMN restart_required INTEGER DEFAULT 0")
            except:
                pass  # Column already exists

            # Mark all users as requiring restart
            self.cursor.execute("""
                UPDATE users SET restart_required = 1 
                WHERE telegram_id IS NOT NULL AND telegram_id != 0
            """)
            
            restart_count = self.cursor.rowcount
            self.conn.commit()
            print(f"✅ Marked {restart_count} users for restart")
            return restart_count
        except Exception as e:
            print(f"DB Error (mark_all_users_for_restart): {e}")
            return 0

    def user_needs_restart(self, telegram_id):
        """Check if user needs to /start again after admin restart"""
        try:
            self.cursor.execute("""
                SELECT restart_required FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = self.cursor.fetchone()
            return row[0] == 1 if row else False
        except Exception as e:
            print(f"DB Error (user_needs_restart): {e}")
            return False

    def clear_restart_flag(self, telegram_id):
        """Clear restart flag when user uses /start"""
        try:
            self.cursor.execute("""
                UPDATE users SET restart_required = 0 WHERE telegram_id = ?
            """, (telegram_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (clear_restart_flag): {e}")
            return False

    def close(self):
        """Close database connection"""
        self.conn.close()