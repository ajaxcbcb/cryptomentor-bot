"""
Database management for CryptoMentor AI Bot
Handles user data, credits, premium status with Supabase integration
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Import SupabaseUsers with fallback
try:
    from supabase_users import SupabaseUsers
except ImportError:
    print("⚠️ SupabaseUsers module not found. Using local fallback.")
    SupabaseUsers = None


class Database:
    def __init__(self):
        """Initialize database with Supabase integration"""
        self.db_path = 'cryptomentor.db'
        self.conn = None
        self.cursor = None
        
        # Initialize Supabase for user management
        self.supabase_users = SupabaseUsers() if SupabaseUsers else None
        
        # Initialize backup system
        self.backup_users = {}
        self.restart_flags = set()

        try:
            self._ensure_directory()
            self._connect()
            self.create_tables()
            
            # Test Supabase connection
            if self.supabase_users and self.supabase_users.test_connection():
                print("✅ Database initialized with Supabase integration")
            else:
                print("⚠️ Database initialized with local fallback only")

        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            self._emergency_recovery()

    def _ensure_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            raise

    def _emergency_recovery(self):
        """Attempt emergency recovery"""
        print("🚨 Entering emergency recovery mode")
        try:
            self._connect()
            self.create_tables()
            print("✅ Emergency recovery completed")
        except Exception as e:
            print(f"❌ Emergency recovery failed: {e}")

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            # Create users table with all required columns (COMPLETE SCHEMA)
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
                    premium_referral_code TEXT,
                    premium_earnings INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP
                )
            """)

            # Get current table schema
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]
            print(f"Current table columns: {columns}")

            # Add missing columns one by one with error handling
            missing_columns = [
                ('telegram_id', 'INTEGER UNIQUE'),
                ('language_code', "TEXT DEFAULT 'id'"),
                ('is_premium', 'INTEGER DEFAULT 0'),
                ('credits', 'INTEGER DEFAULT 0'),
                ('subscription_end', 'TEXT'),
                ('referred_by', 'INTEGER'),
                ('referral_code', 'TEXT'),
                ('premium_referral_code', 'TEXT'),
                ('premium_earnings', 'INTEGER DEFAULT 0'),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('last_seen', 'TIMESTAMP')
            ]

            for column_name, column_def in missing_columns:
                if column_name not in columns:
                    try:
                        self.cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                        print(f"✅ Added missing column: {column_name}")
                    except Exception as col_error:
                        print(f"⚠️ Column {column_name} might already exist or error during add: {col_error}")

        except Exception as e:
            print(f"❌ CRITICAL: Error in table schema migration for 'users': {e}")
            print("🔧 SAFE MODE: Attempting to preserve user data during schema update...")

            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_table = f"users_backup_{timestamp}"

                self.cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM users")
                print(f"✅ Emergency backup created: {backup_table}")

                self.cursor.execute("DROP TABLE users")
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
                        premium_referral_code TEXT,
                        premium_earnings INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP
                    )
                """)

                self.cursor.execute(f"""
                    INSERT INTO users (telegram_id, first_name, last_name, username, language_code,
                                     is_premium, credits, subscription_end, referred_by, referral_code,
                                     premium_referral_code, premium_earnings, created_at, updated_at, last_seen)
                    SELECT telegram_id,
                           COALESCE(first_name, 'User'),
                           last_name,
                           COALESCE(username, 'no_username'),
                           COALESCE(language_code, 'id'),
                           COALESCE(is_premium, 0),
                           COALESCE(credits, 100),
                           subscription_end,
                           referred_by,
                           referral_code,
                           premium_referral_code,
                           COALESCE(premium_earnings, 0),
                           COALESCE(created_at, datetime('now')),
                           COALESCE(updated_at, datetime('now')),
                           last_seen
                    FROM {backup_table}
                    WHERE telegram_id IS NOT NULL AND telegram_id != 0
                """)
                restored_count = self.cursor.rowcount
                print(f"✅ RESTORED {restored_count} users with ALL PREMIUM STATUS PRESERVED")

            except Exception as recovery_error:
                print(f"❌ RECOVERY FAILED: {recovery_error}")
                print("🚨 EMERGENCY: Keeping existing table to prevent data loss")

        # Create subscriptions table
        try:
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
        except Exception as e:
            print(f"Error creating subscriptions table: {e}")


        # Create portfolio table
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARYKEY AUTOINCREMENT,
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
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            """)

            # Create premium referrals table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS premium_referrals (
                    id INTEGER PRIMARYKEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    subscription_type TEXT,
                    subscription_amount INTEGER,
                    earnings INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
                )
            """)

            # Check if user_id column exists in user_activity
            self.cursor.execute("PRAGMA table_info(user_activity)")
            activity_columns = [column[1] for column in self.cursor.fetchall()]
            if 'user_id' not in activity_columns:
                print("Adding missing user_id column to user_activity table...")
                self.cursor.execute("ALTER TABLE user_activity ADD COLUMN user_id INTEGER")

        except Exception as e:
            print(f"Error with user_activity table: {e}")

        self.conn.commit()


    def create_user(self, telegram_id, username="", first_name="", last_name="", language_code="id", referred_by=None):
        """Create a new user with Supabase integration and local fallback"""
        try:
            # Primary: Try Supabase first
            supabase_success = self.supabase_users.add_user(
                user_id=telegram_id,
                username=username or 'no_username',
                first_name=first_name or 'Unknown',
                last_name=last_name or '',
                status='free'
            )

            if supabase_success:
                print(f"✅ User {telegram_id} created in Supabase")
                self.log_user_activity(telegram_id, "user_created", f"New user: {first_name}")
                return True
            else:
                print(f"⚠️ Supabase user creation failed, using local fallback for {telegram_id}")

            # Fallback: Local database
            self.cursor.execute("""
                INSERT OR IGNORE INTO users
                (telegram_id, username, first_name, last_name, language_code, credits, is_premium, referred_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 100, 0, ?, ?, ?)
            """, (
                telegram_id,
                username or 'no_username',
                first_name or 'Unknown',
                last_name or '',
                language_code or 'id',
                referred_by,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            self.conn.commit()

            # Immediate backup of new user
            self.backup_user_data(telegram_id)

            # Verify creation
            created_user = self.get_user(telegram_id)
            if created_user:
                print(f"✅ User {telegram_id} created in local database")
                self.log_user_activity(telegram_id, "user_created", f"New user: {first_name}")
                return True
            else:
                print(f"❌ User creation verification failed for {telegram_id}")
                return False

        except Exception as e:
            print(f"❌ Error creating user {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def get_user(self, telegram_id):
        """Get user data with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase first
            supabase_user = self.supabase_users.get_user(telegram_id)
            if supabase_user:
                # Ensure the user data from Supabase is in a format consistent with local DB if needed
                # For now, assume it's directly usable or map fields if necessary
                return supabase_user

            # Fallback: Local database
            self.cursor.execute("""
                SELECT telegram_id, first_name, last_name, username, language_code,
                       is_premium, credits, subscription_end, referred_by, referral_code, created_at, updated_at, last_seen
                FROM users WHERE telegram_id = ?
            """, (telegram_id,))

            user_data = self.cursor.fetchone()

            if user_data:
                # Convert to dictionary for easier handling
                columns = [description[0] for description in self.cursor.description]
                user_dict = dict(zip(columns, user_data))

                # Update last_seen in local DB
                self.cursor.execute("""
                    UPDATE users SET last_seen = ? WHERE telegram_id = ?
                """, (datetime.now().isoformat(), telegram_id))
                self.conn.commit()

                return user_dict
            else:
                # Try to recover from backup
                if telegram_id in self.backup_users:
                    print(f"🔄 Recovering user {telegram_id} from backup")
                    backup_data = self.backup_users[telegram_id]
                    self._restore_user_from_backup(telegram_id, backup_data)
                    return backup_data
                else:
                    return None

        except Exception as e:
            print(f"❌ Error getting user {telegram_id}: {e}")
            # Try backup recovery as a last resort
            return self.backup_users.get(telegram_id, None)

    def update_user_info(self, telegram_id, username=None, first_name=None, last_name=None, language_code=None):
        """Update user information without affecting credits or premium status"""
        try:
            updates = []
            params = []

            if username is not None:
                updates.append("username = ?")
                params.append(username[:32] if username else 'no_username')

            if first_name is not None:
                updates.append("first_name = ?")
                params.append(first_name[:50] if first_name else 'Unknown')

            if last_name is not None:
                updates.append("last_name = ?")
                params.append(last_name[:50] if last_name else None)

            if language_code is not None:
                updates.append("language_code = ?")
                params.append(language_code[:5] if language_code else 'id')

            if updates:
                params.append(telegram_id)
                query = f"UPDATE users SET {', '.join(updates)}, updated_at = ? WHERE telegram_id = ?"
                params.append(datetime.now().isoformat())
                self.cursor.execute(query, params)
                self.conn.commit()
                print(f"✅ Updated info for user {telegram_id}")
                self.backup_user_data(telegram_id) # Backup after update
                return True
            return True
        except Exception as e:
            print(f"❌ Error updating user info: {e}")
            return False

    def add_user(self, telegram_id, first_name, last_name, username, language_code='id'):
        """Add a new user to the database"""
        # This method might be redundant if create_user handles all cases,
        # but keeping it for specific insertion logic if needed.
        # Primarily relying on create_user which uses Supabase first.
        return self.create_user(telegram_id, username, first_name, last_name, language_code)

    def is_user_premium(self, telegram_id):
        """Check if user has premium status with Supabase first, local fallback"""
        try:
            # Primary: Check Supabase
            is_premium_supabase = self.supabase_users.is_user_premium(telegram_id)
            if is_premium_supabase is not None:
                return is_premium_supabase

            # Fallback: Local database
            user = self.get_user(telegram_id)
            if user:
                is_premium = user.get('is_premium', 0)
                subscription_end = user.get('subscription_end')

                # Check if premium has expired (only if subscription_end is set)
                if is_premium and subscription_end:
                    try:
                        end_date = datetime.fromisoformat(subscription_end)
                        if datetime.now() > end_date:
                            # Premium expired, update status locally
                            self.cursor.execute("""
                                UPDATE users SET is_premium = 0, subscription_end = NULL WHERE telegram_id = ?
                            """, (telegram_id,))
                            self.conn.commit()
                            print(f"✅ Expired premium status updated for {telegram_id} locally.")
                            return False
                    except ValueError:
                        # Invalid date format, treat as potentially active premium if `is_premium` is set
                        print(f"⚠️ Invalid subscription_end format for {telegram_id}, treating as active premium.")
                        pass # Keep is_premium status as is

                return bool(is_premium)
            else:
                return False

        except Exception as e:
            print(f"❌ Error checking premium status for {telegram_id}: {e}")
            return False

    def grant_premium_access(self, telegram_id, granted_by_id, days=30):
        """Grant premium access to a user"""
        try:
            # Primary: Try Supabase
            if days is None or days == 0: # Permanent premium
                supabase_success = self.supabase_users.grant_lifetime_premium(telegram_id)
            else:
                supabase_success = self.supabase_users.grant_premium(telegram_id, days)

            if supabase_success:
                print(f"✅ Granted premium to user {telegram_id} in Supabase.")
                self.log_user_activity(telegram_id, "premium_granted_supabase", f"Granted {'lifetime' if days is None else f'{days} days'} premium")
                return True

            # Fallback: Local database
            if days is None or days == 0:
                end_date_str = None
                plan_type = 'permanent'
            else:
                end_date = datetime.now() + timedelta(days=days)
                end_date_str = end_date.isoformat()
                plan_type = 'premium'

            self.cursor.execute("""
                UPDATE users SET is_premium = 1, subscription_end = ?, updated_at = ? WHERE telegram_id = ?
            """, (end_date_str, datetime.now().isoformat(), telegram_id))

            # Log the subscription locally if not done via Supabase
            self.cursor.execute("""
                INSERT INTO subscriptions (telegram_id, plan, status, end_date, granted_by)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, plan_type, 'active', end_date_str, granted_by_id))

            self.conn.commit()
            self.backup_user_data(telegram_id)
            print(f"✅ Granted {'permanent' if days is None else f'{days} days'} premium to user {telegram_id} locally.")
            self.log_user_activity(telegram_id, "premium_granted", f"Granted {'permanent' if days is None else f'{days} days'} premium")
            return True

        except Exception as e:
            print(f"❌ Error granting premium access to {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def revoke_premium_access(self, telegram_id, revoked_by_id):
        """Revoke premium access from a user"""
        try:
            # Primary: Try Supabase
            supabase_success = self.supabase_users.revoke_premium(telegram_id)
            if supabase_success:
                print(f"✅ Revoked premium from user {telegram_id} in Supabase.")
                self.log_user_activity(telegram_id, "premium_revoked_supabase", "Premium status revoked")
                return True

            # Fallback: Local database
            self.cursor.execute("""
                UPDATE users SET is_premium = 0, subscription_end = NULL, updated_at = ? WHERE telegram_id = ?
            """, (datetime.now().isoformat(), telegram_id))

            # Update subscription status locally if not handled by Supabase
            self.cursor.execute("""
                UPDATE subscriptions SET status = 'revoked'
                WHERE telegram_id = ? AND status = 'active'
            """, (telegram_id,))

            self.conn.commit()
            self.backup_user_data(telegram_id)
            print(f"✅ Revoked premium from user {telegram_id} locally.")
            self.log_user_activity(telegram_id, "premium_revoked", "Premium status revoked")
            return True

        except Exception as e:
            print(f"❌ Error revoking premium access from {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def get_user_portfolio(self, telegram_id):
        """Get user's portfolio"""
        # Note: Supabase integration for portfolio is not specified, so this remains local DB focused.
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
        # Note: Supabase integration for portfolio is not specified.
        try:
            self.cursor.execute("""
                SELECT amount, avg_buy_price FROM portfolio
                WHERE telegram_id = ? AND symbol = ?
            """, (telegram_id, symbol))
            existing = self.cursor.fetchone()

            if existing:
                old_amount, old_price = existing
                new_amount = old_amount + amount
                new_avg_price = ((old_amount * old_price) + (amount * avg_buy_price)) / new_amount
                self.cursor.execute("""
                    UPDATE portfolio SET amount = ?, avg_buy_price = ?
                    WHERE telegram_id = ? AND symbol = ?
                """, (new_amount, new_avg_price, telegram_id, symbol))
            else:
                self.cursor.execute("""
                    INSERT INTO portfolio (telegram_id, symbol, amount, avg_buy_price)
                    VALUES (?, ?, ?, ?)
                """, (telegram_id, symbol, amount, avg_buy_price))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (add_portfolio_item): {e}")
            return False

    def log_user_activity(self, user_id, action, details=None):
        """Log user activity"""
        try:
            self.cursor.execute("""
                INSERT INTO user_activity (user_id, action, details, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, details, datetime.now().isoformat()))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging user activity: {e}")
            return False

    def log_auto_signal_broadcast(self, signals_count, users_reached, total_eligible):
        """Log auto signal broadcast for monitoring"""
        try:
            details = f"Signals: {signals_count}, Reached: {users_reached}/{total_eligible}"
            self.cursor.execute("""
                INSERT INTO user_activity (user_id, action, details, timestamp)
                VALUES (?, ?, ?, ?)
            """, (0, "auto_signal_broadcast", details, datetime.now().isoformat())) # Using user_id 0 for bot actions
            self.conn.commit()
            print(f"[AUTO-SIGNAL SND] 📝 Broadcast logged: {details}")
            return True
        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Error logging broadcast: {e}")
            return False

    def get_user_stats(self):
        """Get user statistics for admin panel (local fallback)"""
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
        """Get user's current credits with Supabase first, local fallback"""
        try:
            # Primary: Check Supabase
            credits_supabase = self.supabase_users.get_user_credits(telegram_id)
            if credits_supabase is not None:
                return credits_supabase

            # Fallback: Local database
            user = self.get_user(telegram_id)
            if user:
                credits = user.get('credits')
                if credits is None:
                    # Fix NULL credits in local DB
                    self.cursor.execute("""
                        UPDATE users SET credits = 100 WHERE telegram_id = ?
                    """, (telegram_id,))
                    self.conn.commit()
                    print(f"🔧 Fixed NULL credits for user {telegram_id} in local DB")
                    return 100
                return max(0, credits)  # Ensure non-negative
            else:
                return 0
        except Exception as e:
            print(f"❌ Error getting credits for {telegram_id}: {e}")
            return 0

    def add_credits(self, telegram_id, amount):
        """Add credits to user account with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_success = self.supabase_users.add_user_credits(telegram_id, amount)
            if supabase_success:
                print(f"✅ Added {amount} credits to user {telegram_id} in Supabase")
                self.log_user_activity(telegram_id, "credits_added", f"Added {amount} credits")
                return True

            # Fallback: Local database
            current_credits = self.get_user_credits(telegram_id)
            new_credits = current_credits + amount

            self.cursor.execute("""
                UPDATE users SET credits = ?, updated_at = ? WHERE telegram_id = ?
            """, (new_credits, datetime.now().isoformat(), telegram_id))

            self.conn.commit()
            self.backup_user_data(telegram_id) # Backup after update

            print(f"✅ Added {amount} credits to user {telegram_id} locally (Total: {new_credits})")
            self.log_user_activity(telegram_id, "credits_added", f"Added {amount} credits")
            return True

        except Exception as e:
            print(f"❌ Error adding credits to {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def deduct_credit(self, telegram_id, amount):
        """Deduct credits from user account with Supabase first, local fallback"""
        try:
            # Check current credits first
            current_credits = self.get_user_credits(telegram_id)

            if current_credits < amount:
                print(f"❌ Insufficient credits for user {telegram_id}: {current_credits} < {amount}")
                return False

            # Primary: Try Supabase
            supabase_success = self.supabase_users.deduct_user_credits(telegram_id, amount)
            if supabase_success:
                print(f"✅ Deducted {amount} credits from user {telegram_id} in Supabase")
                self.log_user_activity(telegram_id, "credits_deducted", f"Deducted {amount} credits")
                return True

            # Fallback: Local database
            new_credits = current_credits - amount

            self.cursor.execute("""
                UPDATE users SET credits = ?, updated_at = ? WHERE telegram_id = ?
            """, (new_credits, datetime.now().isoformat(), telegram_id))

            self.conn.commit()
            self.backup_user_data(telegram_id) # Backup after update

            print(f"✅ Deducted {amount} credits from user {telegram_id} locally (Remaining: {new_credits})")
            self.log_user_activity(telegram_id, "credits_deducted", f"Deducted {amount} credits")
            return True

        except Exception as e:
            print(f"❌ Error deducting credits from {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def grant_premium(self, telegram_id, days):
        """Grant premium status to user with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_success = self.supabase_users.grant_premium(telegram_id, days)
            if supabase_success:
                print(f"✅ Granted {days} days premium to user {telegram_id} in Supabase")
                self.log_user_activity(telegram_id, "premium_granted", f"Granted {days} days premium")
                return True

            # Fallback: Local database
            subscription_end = (datetime.now() + timedelta(days=days)).isoformat()

            self.cursor.execute("""
                UPDATE users SET
                is_premium = 1,
                subscription_end = ?,
                updated_at = ?
                WHERE telegram_id = ?
            """, (subscription_end, datetime.now().isoformat(), telegram_id))

            self.conn.commit()
            self.backup_user_data(telegram_id)

            print(f"✅ Granted {days} days premium to user {telegram_id} locally")
            self.log_user_activity(telegram_id, "premium_granted", f"Granted {days} days premium")
            return True

        except Exception as e:
            print(f"❌ Error granting premium to {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def grant_permanent_premium(self, telegram_id):
        """Grant permanent premium status with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_success = self.supabase_users.grant_lifetime_premium(telegram_id)
            if supabase_success:
                print(f"✅ Granted lifetime premium to user {telegram_id} in Supabase")
                self.log_user_activity(telegram_id, "permanent_premium_granted", "Granted permanent premium")
                return True

            # Fallback: Local database
            self.cursor.execute("""
                UPDATE users SET
                is_premium = 1,
                subscription_end = NULL,
                updated_at = ?
                WHERE telegram_id = ?
            """, (datetime.now().isoformat(), telegram_id))

            self.conn.commit()
            self.backup_user_data(telegram_id)

            print(f"✅ Granted permanent premium to user {telegram_id} locally")
            self.log_user_activity(telegram_id, "permanent_premium_granted", "Granted permanent premium")
            return True

        except Exception as e:
            print(f"❌ Error granting permanent premium to {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def revoke_premium(self, telegram_id):
        """Revoke premium status from user with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_success = self.supabase_users.revoke_premium(telegram_id)
            if supabase_success:
                print(f"✅ Revoked premium from user {telegram_id} in Supabase")
                self.log_user_activity(telegram_id, "premium_revoked", "Premium status revoked")
                return True

            # Fallback: Local database
            self.cursor.execute("""
                UPDATE users SET
                is_premium = 0,
                subscription_end = ?,
                updated_at = ?
                WHERE telegram_id = ?
            """, (datetime.now().isoformat(), datetime.now().isoformat(), telegram_id))

            self.conn.commit()
            self.backup_user_data(telegram_id)

            print(f"✅ Revoked premium from user {telegram_id} locally")
            self.log_user_activity(telegram_id, "premium_revoked", "Premium status revoked")
            return True

        except Exception as e:
            print(f"❌ Error revoking premium from {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def get_all_users(self):
        """Get all users for broadcast purposes with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_users_list = self.supabase_users.get_all_users()
            if supabase_users_list:
                return supabase_users_list

            # Fallback: Local database
            self.cursor.execute("""
                SELECT telegram_id, username, first_name, is_premium FROM users
            """)

            users = []
            for row in self.cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'is_premium': bool(row[3])
                })

            return users

        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []

    def get_eligible_auto_signal_users(self):
        """Get users eligible for auto signals (admin + lifetime) with Supabase first"""
        try:
            # Primary: Try Supabase
            supabase_eligible_users = self.supabase_users.get_eligible_auto_signal_users()
            if supabase_eligible_users:
                return supabase_eligible_users

            # Fallback: Local database (as a fallback for premium users if admin is not found or Supabase fails)
            # Note: Original logic included admin, which is not directly queryable here without env var.
            # We'll fetch premium users as a broad fallback.
            self.cursor.execute("""
                SELECT telegram_id, first_name, username FROM users WHERE is_premium = 1
            """)

            users = []
            for row in self.cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'telegram_id': row[0],
                    'first_name': row[1] or 'User',
                    'username': row[2],
                    'type': 'premium_fallback' # Indicate this is a fallback
                })

            return users

        except Exception as e:
            print(f"❌ Error getting eligible auto signal users: {e}")
            return []

    def get_bot_statistics(self):
        """Get comprehensive bot statistics with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_stats = self.supabase_users.get_bot_statistics()
            if supabase_stats and supabase_stats.get('total_users', 0) > 0:
                return supabase_stats

            # Fallback: Local database
            stats = {}

            # Total users
            self.cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = self.cursor.fetchone()[0]

            # Premium users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            stats['premium_users'] = self.cursor.fetchone()[0]

            # Active users today (based on last_seen)
            today_str = datetime.now().date().isoformat()
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_seen) = ?", (today_str,))
            stats['active_today'] = self.cursor.fetchone()[0]

            # Total credits distributed
            self.cursor.execute("SELECT SUM(credits) FROM users")
            result = self.cursor.fetchone()[0]
            stats['total_credits'] = result if result else 0

            # Average credits per user
            if stats['total_users'] > 0:
                stats['avg_credits'] = stats['total_credits'] / stats['total_users']
            else:
                stats['avg_credits'] = 0

            # Activity stats (commands today)
            self.cursor.execute("SELECT COUNT(*) FROM user_activity WHERE DATE(timestamp) = ?", (today_str,))
            stats['commands_today'] = self.cursor.fetchone()[0]

            # Analysis count (approximated from user_activity actions)
            self.cursor.execute("SELECT COUNT(*) FROM user_activity WHERE action LIKE '%analyze%'")
            stats['analyses_count'] = self.cursor.fetchone()[0]

            return stats

        except Exception as e:
            print(f"❌ Error getting bot statistics: {e}")
            return {
                'total_users': 0,
                'premium_users': 0,
                'active_today': 0,
                'total_credits': 0,
                'avg_credits': 0,
                'commands_today': 0,
                'analyses_count': 0
            }

    def get_recent_activity(self, limit=10):
        """Get recent user activity"""
        # Note: Supabase integration for this is not specified.
        try:
            self.cursor.execute("""
                SELECT user_id, action, details, timestamp
                FROM user_activity
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'action': row[1],
                    'details': row[2],
                    'timestamp': row[3]
                })
            return results
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []

    def revoke_premium(self, user_id):
        """Revoke premium status from user"""
        # This method is an alias for revoke_premium_access
        return self.revoke_premium_access(user_id, None) # None for revoked_by_id

    def fix_all_user_credits(self):
        """Fix all users with NULL or negative credits (local DB operation)"""
        try:
            # Fix NULL credits
            self.cursor.execute("UPDATE users SET credits = 100 WHERE credits IS NULL")
            null_fixed = self.cursor.rowcount

            # Fix negative credits
            self.cursor.execute("UPDATE users SET credits = 10 WHERE credits < 0")
            negative_fixed = self.cursor.rowcount

            self.conn.commit()

            total_fixed = null_fixed + negative_fixed
            print(f"✅ Fixed credits for {total_fixed} users (NULL: {null_fixed}, Negative: {negative_fixed}) in local DB")
            return total_fixed
        except Exception as e:
            print(f"Error fixing all user credits: {e}")
            return 0

    def mark_all_users_for_restart(self):
        """Mark all users as needing restart by logging an event"""
        try:
            current_time = datetime.now().isoformat()
            self.cursor.execute("SELECT telegram_id FROM users")
            users = self.cursor.fetchall()

            for user in users:
                user_id = user[0]
                self.log_user_activity(user_id, "restart_required", f"Bot restart at {current_time}")

            print(f"✅ Marked {len(users)} users for restart in local activity log")
            return len(users)
        except Exception as e:
            print(f"Error marking users for restart: {e}")
            return 0

    def user_needs_restart(self, user_id):
        """Check if user needs to restart after admin restart (checks local activity log)"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM user_activity
                WHERE user_id = ? AND action = 'restart_required'
                AND timestamp > (
                    SELECT COALESCE(MAX(timestamp), '1970-01-01')
                    FROM user_activity
                    WHERE user_id = ? AND action = 'user_reactivated'
                )
            """, (user_id, user_id))

            needs_restart = self.cursor.fetchone()[0] > 0
            return needs_restart
        except Exception as e:
            print(f"Error checking restart status for user {user_id}: {e}")
            return False

    def clear_restart_flag(self, user_id):
        """Clear restart flag for user (handled by logging 'user_reactivated')"""
        try:
            self.log_user_activity(user_id, "user_reactivated", f"User acknowledged restart/re-activated.")
            return True
        except Exception as e:
            print(f"Error clearing restart flag for user {user_id}: {e}")
            return False

    def refresh_all_free_user_credits(self):
        """Give bonus credits to all free users (local DB operation)"""
        try:
            self.cursor.execute("""
                UPDATE users
                SET credits = credits + 50
                WHERE is_premium = 0 AND telegram_id IS NOT NULL
            """)

            refreshed_count = self.cursor.rowcount
            self.conn.commit()

            print(f"✅ Gave +50 credits to {refreshed_count} free users in local DB")
            return refreshed_count
        except Exception as e:
            print(f"Error refreshing free user credits: {e}")
            return 0

    def log_auto_signals_broadcast(self, signals_count, success_count, total_eligible):
        """Log auto signals broadcast for tracking (local DB operation)"""
        try:
            admin_id = int(os.getenv('ADMIN_USER_ID', '0')) # Use 0 or a specific bot admin ID
            details = f"Sent {signals_count} signals to {success_count}/{total_eligible} eligible users"

            self.cursor.execute("""
                INSERT INTO user_activity (user_id, action, details, timestamp)
                VALUES (?, ?, ?, ?)
            """, (admin_id, "auto_signals_broadcast", details, datetime.now().isoformat()))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging auto signals broadcast: {e}")
            return False

    def get_user_by_referral_code(self, referral_code):
        """Get user ID by referral code (local DB operation)"""
        try:
            self.cursor.execute("""
                SELECT telegram_id FROM users WHERE referral_code = ?
            """, (referral_code,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"DB Error (get_user_by_referral_code): {e}")
            return None

    def update_user_language(self, telegram_id, language):
        """Update user language preference"""
        # This logic might be better handled by `update_user_info`
        # but keeping it if it has specific use cases.
        try:
            self.cursor.execute("""
                UPDATE users SET language_code = ?, updated_at = ? WHERE telegram_id = ?
            """, (language, datetime.now().isoformat(), telegram_id))

            success = self.cursor.rowcount > 0
            if success:
                self.conn.commit()
                self.backup_user_data(telegram_id)
            return success
        except Exception as e:
            print(f"DB Error (update_user_language): {e}")
            return False

    def get_bot_statistics(self):
        """Get comprehensive bot statistics with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_stats = self.supabase_users.get_bot_statistics()
            if supabase_stats and supabase_stats.get('total_users', 0) > 0:
                return supabase_stats

            # Fallback: Local database
            stats = {}

            self.cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            stats['premium_users'] = self.cursor.fetchone()[0]

            today_str = datetime.now().date().isoformat()
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_seen) = ?", (today_str,))
            stats['active_today'] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT SUM(credits) FROM users")
            result = self.cursor.fetchone()[0]
            stats['total_credits'] = result if result else 0

            if stats['total_users'] > 0:
                stats['avg_credits'] = stats['total_credits'] / stats['total_users']
            else:
                stats['avg_credits'] = 0

            self.cursor.execute("SELECT COUNT(*) FROM user_activity WHERE DATE(timestamp) = ?", (today_str,))
            stats['commands_today'] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM user_activity WHERE action LIKE '%analyze%'")
            stats['analyses_count'] = self.cursor.fetchone()[0]

            return stats

        except Exception as e:
            print(f"❌ Error getting bot statistics: {e}")
            return {
                'total_users': 0, 'premium_users': 0, 'active_today': 0,
                'total_credits': 0, 'avg_credits': 0, 'commands_today': 0, 'analyses_count': 0
            }

    def get_user_by_premium_referral_code(self, premium_code):
        """Get user ID by premium referral code (local DB operation)"""
        try:
            self.cursor.execute("""
                SELECT telegram_id FROM users WHERE premium_referral_code = ?
            """, (premium_code,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"DB Error (get_user_by_premium_referral_code): {e}")
            return None

    def get_user_referral_codes(self, telegram_id):
        """Get both referral codes for a user (local DB operation)"""
        try:
            self.cursor.execute("""
                SELECT referral_code, premium_referral_code FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = self.cursor.fetchone()
            if row:
                return {
                    'free_referral_code': row[0],
                    'premium_referral_code': row[1]
                }
            return None
        except Exception as e:
            print(f"DB Error (get_user_referral_codes): {e}")
            return None

    def get_premium_referral_stats(self, telegram_id):
        """Get premium referral statistics for a user (local DB operation)"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(earnings), 0)
                FROM premium_referrals
                WHERE referrer_id = ? AND status = 'paid'
            """, (telegram_id,))

            total_referrals, total_earnings = self.cursor.fetchone()

            self.cursor.execute("""
                SELECT pr.referred_id, u.first_name, pr.subscription_type, pr.earnings, pr.created_at
                FROM premium_referrals pr
                JOIN users u ON pr.referred_id = u.telegram_id
                WHERE pr.referrer_id = ? AND pr.status = 'paid'
                ORDER BY pr.created_at DESC
                LIMIT 5
            """, (telegram_id,))

            recent_referrals = self.cursor.fetchall()

            return {
                'total_referrals': total_referrals or 0,
                'total_earnings': total_earnings or 0,
                'recent_referrals': recent_referrals
            }
        except Exception as e:
            print(f"Error getting premium referral stats: {e}")
            return {'total_referrals': 0, 'total_earnings': 0, 'recent_referrals': []}

    def record_premium_referral_reward(self, referrer_id, referred_id, subscription_type, package_amount):
        """Record premium referral reward when someone subscribes (local DB operation)"""
        try:
            earnings = 10000 # Fixed earning per referral

            self.cursor.execute("""
                INSERT INTO premium_referrals
                (referrer_id, referred_id, subscription_type, subscription_amount, earnings, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'paid', datetime('now'))
            """, (referrer_id, referred_id, subscription_type, package_amount, earnings))

            self.cursor.execute("""
                UPDATE users SET premium_earnings = premium_earnings + ?, updated_at = ? WHERE telegram_id = ?
            """, (earnings, datetime.now().isoformat(), referrer_id))

            self.conn.commit()
            self.log_user_activity(referrer_id, "premium_referral_reward",
                                 f"Earned Rp {earnings:,} from {referred_id} subscribing {subscription_type}")
            return True
        except Exception as e:
            print(f"Error recording premium referral reward: {e}")
            return False

    def check_premium_referral(self, telegram_id):
        """Check if user was referred via premium referral code (local DB operation)"""
        try:
            self.cursor.execute("""
                SELECT referred_by FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Error checking premium referral: {e}")
            return None

    def add_credits(self, telegram_id, amount):
        """Add credits to user account with Supabase first, local fallback"""
        try:
            # Primary: Try Supabase
            supabase_success = self.supabase_users.add_user_credits(telegram_id, amount)
            if supabase_success:
                print(f"✅ Added {amount} credits to user {telegram_id} in Supabase")
                self.log_user_activity(telegram_id, "credits_added", f"Added {amount} credits")
                return True

            # Fallback: Local database
            current_credits = self.get_user_credits(telegram_id)
            new_credits = current_credits + amount

            self.cursor.execute("""
                UPDATE users SET credits = ?, updated_at = ? WHERE telegram_id = ?
            """, (new_credits, datetime.now().isoformat(), telegram_id))

            self.conn.commit()
            self.backup_user_data(telegram_id)

            print(f"✅ Added {amount} credits to user {telegram_id} locally (Total: {new_credits})")
            self.log_user_activity(telegram_id, "credits_added", f"Added {amount} credits")
            return True

        except Exception as e:
            print(f"❌ Error adding credits to {telegram_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def ensure_user_persistence(self, telegram_id, username, first_name, last_name, language_code):
        """Ensure user data persists correctly, creating if not exists"""
        try:
            existing_user = self.get_user(telegram_id)
            if existing_user:
                # Update existing user info
                return self.update_user_info(telegram_id, username, first_name, last_name, language_code)
            else:
                # Create new user
                return self.create_user(telegram_id, username, first_name, last_name, language_code)
        except Exception as e:
            print(f"Error ensuring user persistence: {e}")
            return False

    def backup_user_data(self, telegram_id):
        """Create backup of user data for recovery (in-memory backup)"""
        try:
            user = self.get_user(telegram_id)
            if user:
                self.backup_users[telegram_id] = user # Store a copy
                # Log the backup event for auditing
                self.log_user_activity(telegram_id, "user_backup_created", f"Backup created for user data.")
                return True
            return False
        except Exception as e:
            print(f"Error backing up user data for {telegram_id}: {e}")
            return False

    def _restore_user_from_backup(self, telegram_id, backup_data):
        """Internal method to restore user data from backup (example)"""
        # This is a placeholder for a more robust recovery mechanism.
        # It assumes backup_data is a dictionary of user info.
        print(f"Attempting to restore user {telegram_id} from backup...")
        if not backup_data:
            print(f"No backup data found for user {telegram_id}.")
            return False

        try:
            # Example: Re-create or update user using backup data
            # This might involve calling create_user or update_user_info
            # Ensure to handle potential inconsistencies or missing fields.
            self.create_user(
                telegram_id=backup_data.get('telegram_id'),
                username=backup_data.get('username'),
                first_name=backup_data.get('first_name'),
                last_name=backup_data.get('last_name'),
                language_code=backup_data.get('language_code')
            )
            # You might also need to restore other fields like credits, premium status etc.
            # This is a simplified example.

            self.log_user_activity(telegram_id, "user_restored_from_backup", "User data restored from backup.")
            print(f"User {telegram_id} restoration process initiated from backup.")
            return True
        except Exception as e:
            print(f"Error during _restore_user_from_backup for {telegram_id}: {e}")
            return False

    def recover_user_from_backup(self, telegram_id):
        """Attempt to recover user from backup logs"""
        try:
            user_backup = self.backup_users.get(telegram_id)
            if user_backup:
                return self._restore_user_from_backup(telegram_id, user_backup)
            else:
                print(f"No backup found for user {telegram_id} to recover.")
                return False
        except Exception as e:
            print(f"Error recovering user {telegram_id} from backup: {e}")
            return False

    def set_user_language(self, telegram_id, language):
        """Set user language preference"""
        # This method is an alias for updating language code, potentially via update_user_info.
        return self.update_user_info(telegram_id=telegram_id, language_code=language)

    def create_automatic_backup(self):
        """Create automatic backup of critical user data (local DB operation)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Backup users table
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS users_backup_{timestamp} AS
                SELECT * FROM users WHERE telegram_id IS NOT NULL
            """)

            # Backup premium referrals
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS premium_referrals_backup_{timestamp} AS
                SELECT * FROM premium_referrals
            """)

            self.conn.commit()
            print(f"✅ Automatic backup created: users_backup_{timestamp}")
            return timestamp

        except Exception as e:
            print(f"❌ Error creating automatic backup: {e}")
            return None

    def verify_user_data_integrity(self):
        """Verify user data integrity after updates (local DB operation)"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            premium_count = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1 AND subscription_end IS NULL")
            lifetime_count = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
            corrupt_count = self.cursor.fetchone()[0]

            integrity_report = {
                'premium_users': premium_count,
                'lifetime_users': lifetime_count,
                'corrupt_entries': corrupt_count,
                'integrity_ok': corrupt_count == 0
            }

            print(f"📊 Data Integrity Check: Premium={premium_count}, Lifetime={lifetime_count}, Corrupt={corrupt_count}")
            return integrity_report

        except Exception as e:
            print(f"❌ Error verifying data integrity: {e}")
            return {'integrity_ok': False, 'error': str(e)}

    def close(self):
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
                print("✅ Database connection closed.")
        except Exception as e:
            print(f"Error closing database: {e}")