# Adding the get_eligible_auto_signal_users method to the Database class.
import sqlite3
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="cryptomentor.db"):
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()

            # Initialize Supabase integration
            self.supabase_enabled = False
            try:
                from supabase_client import supabase_service, get_live_user_count, verify_database_integrity
                self.supabase_service = supabase_service
                self.get_live_user_count = get_live_user_count
                self.verify_database_integrity = verify_database_integrity
                self.supabase_enabled = True
                print("✅ Database class integrated with Supabase service role client")
            except Exception as supabase_error:
                print(f"⚠️ Supabase integration failed: {supabase_error}")
                self.supabase_enabled = False

        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise

    def create_tables(self):
        # Check if tables exist and add missing columns if needed
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Get current table schema
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]
            print(f"Current table columns: {columns}")

            # Add missing columns one by one with error handling
            missing_columns = [
                ('telegram_id', 'INTEGER'),
                ('language_code', "TEXT DEFAULT 'id'"),
                ('is_premium', 'INTEGER DEFAULT 0'),
                ('credits', 'INTEGER DEFAULT 0'),
                ('subscription_end', 'TEXT'),
                ('referred_by', 'INTEGER'),
                ('referral_code', 'TEXT'),
                ('premium_referral_code', 'TEXT'),
                ('premium_earnings', 'INTEGER DEFAULT 0')
            ]

            for column_name, column_def in missing_columns:
                if column_name not in columns:
                    try:
                        self.cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                        print(f"✅ Added missing column: {column_name}")
                    except Exception as col_error:
                        print(f"⚠️ Column {column_name} might already exist: {col_error}")

        except Exception as e:
            print(f"❌ CRITICAL: Error in table schema migration: {e}")
            print("🔧 SAFE MODE: Preserving all user data...")

            # SAFE RECOVERY: Always backup before any changes
            try:
                # Create timestamp for backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_table = f"users_backup_{timestamp}"

                # Always create backup first
                self.cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM users")
                print(f"✅ Emergency backup created: {backup_table}")

                # Check if we have users to preserve
                self.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
                user_count = self.cursor.fetchone()[0]

                if user_count > 0:
                    print(f"⚠️ PRESERVING {user_count} users during schema update...")

                    # Recreate table with correct schema
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
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Restore ALL data preserving premium status
                    self.cursor.execute(f"""
                        INSERT INTO users (telegram_id, first_name, last_name, username, language_code, 
                                         is_premium, credits, subscription_end, referred_by, referral_code,
                                         premium_referral_code, premium_earnings, created_at)
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
                               COALESCE(created_at, datetime('now'))
                        FROM {backup_table}
                        WHERE telegram_id IS NOT NULL AND telegram_id != 0
                    """)

                    restored_count = self.cursor.rowcount
                    print(f"✅ RESTORED {restored_count} users with ALL PREMIUM STATUS PRESERVED")

                    # Verify premium users were restored
                    self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
                    premium_count = self.cursor.fetchone()[0]
                    print(f"✅ Premium users verified: {premium_count}")

                else:
                    # Safe to recreate empty table
                    self.cursor.execute("DROP TABLE IF EXISTS users")
                    self.cursor.execute("""
                        CREATE TABLE users (
                            id INTEGER PRIMARYKEY AUTOINCREMENT,
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
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    print("✅ Empty table recreated with complete schema")

            except Exception as recovery_error:
                print(f"❌ RECOVERY FAILED: {recovery_error}")
                # Emergency: Don't drop the table if recovery fails
                print("🚨 EMERGENCY: Keeping existing table to prevent data loss")
                # Try to work with existing structure

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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    def create_user(self, telegram_id, username, first_name=None, last_name=None, language_code='id', referred_by=None):
        """Create a new user in the database with enhanced persistence and Supabase sync"""
        try:
            # Validate telegram_id
            if not telegram_id or telegram_id <= 0:
                print(f"❌ Invalid telegram_id: {telegram_id}")
                return False

            # Check if user already exists
            existing_user = self.get_user(telegram_id)
            if existing_user:
                print(f"✅ User {telegram_id} already exists - updating info if needed")
                # Update user info if provided (keep existing data intact)
                self.update_user_info(telegram_id, username, first_name, last_name, language_code)

                # Sync with Supabase if enabled
                if self.supabase_enabled:
                    try:
                        from supabase_client import add_user
                        sync_result = add_user(
                            user_id=telegram_id,
                            username=username,
                            first_name=first_name,
                            last_name=last_name,
                            is_premium=existing_user.get('is_premium', False)
                        )
                        print(f"🔄 Supabase sync result for existing user: {sync_result['success']}")
                    except Exception as sync_error:
                        print(f"⚠️ Supabase sync failed for existing user: {sync_error}")

                return True

            # Generate unique referral codes
            import random
            import string

            # Generate free referral code
            referral_code = 'F' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            while self.get_user_by_referral_code(referral_code):
                referral_code = 'F' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

            # Generate premium referral code
            premium_referral_code = 'P' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            while self.get_user_by_premium_referral_code(premium_referral_code):
                premium_referral_code = 'P' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

            # Base credits: 100 for all users
            base_credits = 100

            # Bonus credits: +5 if referred
            bonus_credits = 5 if referred_by else 0
            total_credits = base_credits + bonus_credits

            # Clean data before insertion
            clean_username = username[:32] if username else 'no_username'
            clean_first_name = first_name[:50] if first_name else 'Unknown'
            clean_last_name = last_name[:50] if last_name else None
            clean_language = language_code[:5] if language_code else 'id'

            # Insert new user with transaction safety
            self.cursor.execute("BEGIN TRANSACTION")

            self.cursor.execute("""
                INSERT INTO users 
                (telegram_id, first_name, last_name, username, language_code, credits, referral_code, premium_referral_code, referred_by, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (telegram_id, clean_first_name, clean_last_name, clean_username, clean_language, total_credits, referral_code, premium_referral_code, referred_by))

            # Verify insertion
            self.cursor.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
            if not self.cursor.fetchone():
                self.cursor.execute("ROLLBACK")
                print(f"❌ Failed to insert user {telegram_id}")
                return False

            self.cursor.execute("COMMIT")

            # Sync with Supabase if enabled
            if self.supabase_enabled:
                try:
                    from supabase_client import add_user
                    print(f"🔄 Syncing new user {telegram_id} to Supabase...")
                    sync_result = add_user(
                        user_id=telegram_id,
                        username=clean_username,
                        first_name=clean_first_name,
                        last_name=clean_last_name,
                        is_premium=False
                    )

                    if sync_result["success"]:
                        print(f"✅ User {telegram_id} successfully synced to Supabase")
                        # Verify user count immediately
                        if hasattr(self, 'get_live_user_count'):
                            live_count = self.get_live_user_count()
                            print(f"📊 Live Supabase user count after sync: {live_count}")
                    else:
                        print(f"❌ Supabase sync failed: {sync_result.get('error')}")

                except Exception as sync_error:
                    print(f"❌ Critical Supabase sync error: {sync_error}")
                    # Don't fail the whole operation, but log it
                    self.log_user_activity(telegram_id, "supabase_sync_failed", str(sync_error))

            # Log the user creation
            credit_msg = f"New user registered with {total_credits} credits ({base_credits} base"
            if referred_by:
                credit_msg += f" + {bonus_credits} referral bonus"
            credit_msg += ")"
            self.log_user_activity(telegram_id, "user_created", credit_msg)
            print(f"✅ New user {telegram_id} ({clean_username}) created with {total_credits} credits")

            # Create backup entry in activity log for recovery
            self.log_user_activity(telegram_id, "user_backup_created", f"User: {clean_first_name}, Username: {clean_username}, Credits: {total_credits}")

            return True
        except Exception as e:
            try:
                self.cursor.execute("ROLLBACK")
            except:
                pass
            print(f"❌ DB Error (create_user): {e}")
            return False

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
                query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
                self.cursor.execute(query, params)
                self.conn.commit()
                print(f"✅ Updated info for user {telegram_id}")
                return True
            return True
        except Exception as e:
            print(f"❌ Error updating user info: {e}")
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
            """, (0, "auto_signal_broadcast", details, datetime.now().isoformat()))
            self.conn.commit()
            print(f"[AUTO-SIGNAL SND] 📝 Broadcast logged: {details}")
            return True
        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Error logging broadcast: {e}")
            return False

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
        """Get user's current credits"""
        try:
            user = self.get_user(telegram_id)
            if not user:
                print(f"❌ User {telegram_id} not found when getting credits")
                return 0

            credits = user.get('credits')
            if credits is None:
                # Fix NULL credits by setting to default 100
                print(f"⚠️ User {telegram_id} has NULL credits, fixing...")
                self.cursor.execute("UPDATE users SET credits = 100 WHERE telegram_id = ?", (telegram_id,))
                self.conn.commit()
                return 100

            return max(0, credits)  # Ensure credits never go negative
        except Exception as e:
            print(f"Error getting user credits: {e}")
            return 0

    def get_eligible_auto_signal_users(self):
        """Get users eligible for auto signals (admin and lifetime premium)"""
        try:
            admin1_id = 1234500009  # Primary admin
            admin2_id = 7255533151  # Secondary admin
            eligible_users = []

            # Add admins
            eligible_users.extend([
                {'telegram_id': admin1_id, 'type': 'admin', 'first_name': 'Admin1'},
                {'telegram_id': admin2_id, 'type': 'admin', 'first_name': 'Admin2'}
            ])

            # Get lifetime premium users (subscription_end IS NULL means lifetime)
            self.cursor.execute("""
                SELECT telegram_id, first_name FROM users 
                WHERE is_premium = 1 AND subscription_end IS NULL
            """)
            lifetime_users = self.cursor.fetchall()

            for user in lifetime_users:
                if user[0] != admin1_id and user[0] != admin2_id:  # Don't duplicate admins
                    eligible_users.append({
                        'telegram_id': user[0],
                        'first_name': user[1] or 'User',
                        'type': 'lifetime'
                    })

            print(f"👥 Auto signals eligible: Admin1({admin1_id}), Admin2({admin2_id}) + {len(lifetime_users)} Lifetime users")
            return eligible_users

        except Exception as e:
            print(f"❌ Error getting eligible auto signal users: {e}")
            return []

    def deduct_credit(self, telegram_id, amount):
        """Deduct credits from user (only for non-premium, non-admin users)"""
        try:
            # Get all admin IDs
            admin_ids = set()
            for i in range(1, 10):
                key = f'ADMIN_USER_ID' if i == 1 else f'ADMIN{i}_USER_ID'
                admin_id_str = os.getenv(key, '0')
                try:
                    admin_id = int(admin_id_str)
                    if admin_id > 0:
                        admin_ids.add(admin_id)
                except ValueError:
                    continue

            if self.is_user_premium(telegram_id) or telegram_id in admin_ids:
                # Admins and premium users don't lose credits
                return True

            # Check current credits first to ensure user has enough
            current_user = self.get_user(telegram_id)
            if not current_user:
                return False

            current_credits = current_user.get('credits', 0)
            if current_credits < amount:
                print(f"❌ Insufficient credits for user {telegram_id}: has {current_credits}, needs {amount}")
                return False

            self.cursor.execute("""
                UPDATE users SET credits = credits - ? 
                WHERE telegram_id = ? AND credits >= ?
            """, (amount, telegram_id, amount))

            if self.cursor.rowcount > 0:
                self.conn.commit()
                # Log credit deduction for tracking
                self.log_user_activity(telegram_id, "credit_deduction", f"Deducted {amount} credits, remaining: {current_credits - amount}")
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
                SELECT COUNT(DISTINCT user_id) FROM user_activity 
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

    def grant_premium_by_package(self, telegram_id, package_type):
        """Grant premium based on package type"""
        package_days = {
            '1_month': 30,
            '2_months': 60,
            '6_months': 180,
            '1_year': 365,
            'lifetime': None  # None means permanent
        }

        days = package_days.get(package_type)
        if days is None and package_type == 'lifetime':
            return self.grant_permanent_premium(telegram_id)
        elif days is not None:
            return self.grant_premium(telegram_id, days)
        else:
            return False

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
            return row[0] if row else None
        except Exception as e:
            print(f"DB Error (get_user_by_referral_code): {e}")
            return None



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
                SELECT COUNT(DISTINCT user_id) FROM user_activity 
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
        try:
            self.cursor.execute("""
                UPDATE users 
                SET is_premium = 0, subscription_end = NULL 
                WHERE telegram_id = ?
            """, (user_id,))

            success = self.cursor.rowcount > 0
            if success:
                self.conn.commit()
                print(f"✅ Premium revoked for user {user_id}")

            return success
        except Exception as e:
            print(f"Error revoking premium for user {user_id}: {e}")
            return False

    def fix_all_user_credits(self):
        """Fix all users with NULL or negative credits"""
        try:
            # Fix NULL credits
            self.cursor.execute("UPDATE users SET credits = 100 WHERE credits IS NULL")
            null_fixed = self.cursor.rowcount

            # Fix negative credits
            self.cursor.execute("UPDATE users SET credits = 10 WHERE credits < 0")
            negative_fixed = self.cursor.rowcount

            self.conn.commit()

            total_fixed = null_fixed + negative_fixed
            print(f"✅ Fixed credits for {total_fixed} users (NULL: {null_fixed}, Negative: {negative_fixed})")

            return total_fixed
        except Exception as e:
            print(f"Error fixing all user credits: {e}")
            return 0

    def fix_referral_data_integrity(self):
        """Fix missing referral codes and other referral-related issues"""
        try:
            import random
            import string

            fixed_count = 0

            # Get users with missing referral codes
            self.cursor.execute("""
                SELECT telegram_id, username, first_name 
                FROM users 
                WHERE (referral_code IS NULL OR premium_referral_code IS NULL) 
                AND telegram_id IS NOT NULL
            """)

            users_to_fix = self.cursor.fetchall()

            for user in users_to_fix:
                telegram_id, username, first_name = user

                # Generate referral codes if missing
                self.cursor.execute("SELECT referral_code, premium_referral_code FROM users WHERE telegram_id = ?", (telegram_id,))
                codes = self.cursor.fetchone()

                referral_code = codes[0] if codes and codes[0] else None
                premium_referral_code = codes[1] if codes and codes[1] else None

                # Generate free referral code if missing
                if not referral_code:
                    referral_code = 'F' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
                    while self.get_user_by_referral_code(referral_code):
                        referral_code = 'F' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

                # Generate premium referral code if missing
                if not premium_referral_code:
                    premium_referral_code = 'P' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
                    while self.get_user_by_premium_referral_code(premium_referral_code):
                        premium_referral_code = 'P' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

                # Update the user
                self.cursor.execute("""
                    UPDATE users 
                    SET referral_code = COALESCE(referral_code, ?),
                        premium_referral_code = COALESCE(premium_referral_code, ?)
                    WHERE telegram_id = ?
                """, (referral_code, premium_referral_code, telegram_id))

                if self.cursor.rowcount > 0:
                    fixed_count += 1
                    print(f"✅ Fixed referral codes for user {telegram_id} ({first_name})")

            self.conn.commit()
            print(f"✅ Fixed referral data for {fixed_count} users")
            return fixed_count

        except Exception as e:
            print(f"❌ Error fixing referral data integrity: {e}")
            return 0

    def mark_all_users_for_restart(self):
        """Mark all users as needing restart"""
        try:
            # Add a restart flag to user activity
            current_time = datetime.now().isoformat()

            # Get all users
            self.cursor.execute("SELECT telegram_id FROM users")
            users = self.cursor.fetchall()

            for user in users:
                user_id = user[0]
                self.log_user_activity(user_id, "restart_required", f"Bot restart at {current_time}")

            print(f"✅ Marked {len(users)} users for restart")
            return len(users)
        except Exception as e:
            print(f"Error marking users for restart: {e}")
            return 0

    def user_needs_restart(self, user_id):
        """Check if user needs to restart after admin restart"""
        try:
            # Check if user has restart_required flag and hasn't cleared it
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
        """Clear restart flag for user"""
        try:
            # This is handled by logging the reactivation
            return True
        except Exception as e:
            print(f"Error clearing restart flag for user {user_id}: {e}")
            return False

    def refresh_all_free_user_credits(self):
        """Give +50 credits to all free users (admin mass credit refresh)"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET credits = credits + 50 
                WHERE (subscription_end IS NULL OR subscription_end < datetime('now')) 
                AND credits < 1000
            """)

            refreshed_count = self.cursor.rowcount
            self.conn.commit()

            print(f"✅ Refreshed credits for {refreshed_count} free users")
            return refreshed_count

        except Exception as e:
            print(f"DB Error (refresh_all_free_user_credits): {e}")
            return 0

    def ban_user(self, user_id):
        """Ban a user from using bot commands"""
        try:
            # Add banned column if it doesn't exist
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]

            if 'banned' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN banned BOOLEAN DEFAULT FALSE")
                print("✅ Added 'banned' column to users table")

            # Ban the user
            self.cursor.execute("""
                UPDATE users SET banned = TRUE WHERE telegram_id = ?
            """, (user_id,))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"DB Error (ban_user): {e}")
            return False

    def unban_user(self, user_id):
        """Unban a user to restore bot command access"""
        try:
            # Add banned column if it doesn't exist
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]

            if 'banned' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN banned BOOLEAN DEFAULT FALSE")
                print("✅ Added 'banned' column to users table")

            # Unban the user
            self.cursor.execute("""
                UPDATE users SET banned = FALSE WHERE telegram_id = ?
            """, (user_id,))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"DB Error (unban_user): {e}")
            return False

    def log_auto_signals_broadcast(self, signals_count, success_count, total_eligible):
        """Log auto signals broadcast for tracking"""
        try:
            # Get first available admin ID for logging
            admin_id = 0
            for i in range(1, 10):
                key = f'ADMIN_USER_ID' if i == 1 else f'ADMIN{i}_USER_ID'
                admin_id_str = os.getenv(key, '0')
                try:
                    potential_admin_id = int(admin_id_str)
                    if potential_admin_id > 0:
                        admin_id = potential_admin_id
                        break
                except ValueError:
                    continue

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

    def get_all_users(self):
        """Get all users for broadcast functionality"""
        try:
            self.cursor.execute("""
                SELECT telegram_id, first_name, username, is_premium, created_at
                FROM users 
                WHERE telegram_id IS NOT NULL AND telegram_id != 0
                ORDER BY created_at DESC
            """)

            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'first_name': row[1],
                    'username': row[2],
                    'is_premium': row[3],
                    'created_at': row[4]
                })
            return results
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    def get_user_by_premium_referral_code(self, premium_code):
        """Get user ID by premium referral code"""
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
        """Get both referral codes for a user"""
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
        """Get premium referral statistics for a user"""
        try:
            # Get total premium referrals and earnings
            self.cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(earnings), 0) 
                FROM premium_referrals 
                WHERE referrer_id = ? AND status = 'paid'
            """, (telegram_id,))

            total_referrals, total_earnings = self.cursor.fetchone()

            # Get recent premium referrals
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
        """Record premium referral reward when someone subscribes"""
        try:
            # Validate inputs
            if not referrer_id or not referred_id:
                print(f"❌ Invalid referral IDs: referrer={referrer_id}, referred={referred_id}")
                return False

            # Check if referrer exists and is premium (only premium users can earn money)
            referrer = self.get_user(referrer_id)
            if not referrer:
                print(f"❌ Referrer {referrer_id} not found")
                return False

            if not self.is_user_premium(referrer_id):
                print(f"❌ Referrer {referrer_id} is not premium, cannot earn money rewards")
                return False

            # Calculate earnings (Rp 10,000 per premium subscription)
            earnings = 10000

            # Check if this referral reward already exists to prevent duplicates
            self.cursor.execute("""
                SELECT id FROM premium_referrals 
                WHERE referrer_id = ? AND referred_id = ? AND status = 'paid'
            """, (referrer_id, referred_id))

            if self.cursor.fetchone():
                print(f"⚠️ Premium referral reward already exists for {referrer_id} → {referred_id}")
                return True  # Not an error, just already processed

            self.cursor.execute("""
                INSERT INTO premium_referrals 
                (referrer_id, referred_id, subscription_type, subscription_amount, earnings, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'paid', datetime('now'))
            """, (referrer_id, referred_id, subscription_type, package_amount, earnings))

            # Update referrer's premium earnings
            self.cursor.execute("""
                UPDATE users SET premium_earnings = COALESCE(premium_earnings, 0) + ? WHERE telegram_id = ?
            """, (earnings, referrer_id))

            self.conn.commit()

            # Log the reward
            self.log_user_activity(referrer_id, "premium_referral_reward", 
                                 f"Earned Rp {earnings:,} from {referred_id} subscribing {subscription_type}")

            print(f"✅ Premium referral reward processed: {referrer_id} earned Rp {earnings:,}")
            return True
        except Exception as e:
            print(f"Error recording premium referral reward: {e}")
            return False

    def check_premium_referral(self, telegram_id):
        """Check if user was referred via premium referral code"""
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
        """Add credits to user account"""
        try:
            # Validate amount is positive
            if amount <= 0:
                print(f"❌ Invalid credit amount: {amount}")
                return False

            # Get current credits for logging
            current_user = self.get_user(telegram_id)
            if not current_user:
                print(f"❌ User {telegram_id} not found when adding credits")
                return False

            current_credits = current_user.get('credits', 0)

            self.cursor.execute("""
                UPDATE users SET credits = credits + ? WHERE telegram_id = ?
            """, (amount, telegram_id))

            success = self.cursor.rowcount > 0
            if success:
                self.conn.commit()
                new_total = current_credits + amount
                # Log credit addition for tracking
                self.log_user_activity(telegram_id, "credit_addition", f"Added {amount} credits, new total: {new_total}")
                print(f"✅ Added {amount} credits to user {telegram_id}: {current_credits} → {new_total}")

            return success
        except Exception as e:
            print(f"DB Error (add_credits): {e}")
            return False

    def ensure_user_persistence(self, telegram_id, username, first_name, last_name, language_code):
        """Ensure user data persists correctly"""
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
        """Create backup of user data for recovery"""
        try:
            user = self.get_user(telegram_id)
            if user:
                backup_data = f"User backup: {user}"
                self.log_user_activity(telegram_id, "user_backup", backup_data[:200])
                return True
            return False
        except Exception as e:
            print(f"Error backing up user data: {e}")
            return False

    def recover_user_from_backup(self, telegram_id):
        """Attempt to recover user from backup logs"""
        try:
            # This is a placeholder - implement based on your backup strategy
            self.log_user_activity(telegram_id, "recovery_attempted", f"Recovery attempted for user {telegram_id}")
            return True
        except Exception as e:
            print(f"Error recovering user from backup: {e}")
            return False

    def set_user_language(self, telegram_id, language):
        """Set user language preference"""
        try:
            self.cursor.execute("""
                UPDATE users SET language_code = ? WHERE telegram_id = ?
            """, (language, telegram_id))

            success = self.cursor.rowcount > 0
            if success:
                self.conn.commit()

            return success
        except Exception as e:
            print(f"DB Error (set_user_language): {e}")
            return False

    def create_automatic_backup(self):
        """Create automatic backup of critical user data"""
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
        """Verify user data integrity after updates"""
        try:
            # Check for premium users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            premium_count = self.cursor.fetchone()[0]

            # Check for lifetime users (subscription_end IS NULL)
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1 AND subscription_end IS NULL")
            lifetime_count = self.cursor.fetchone()[0]

            # Check for data corruption
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
            corrupt_count = self.cursor.fetchone()[0]

            # Check for referral data integrity
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code IS NULL AND telegram_id IS NOT NULL")
            missing_referral_codes = self.cursor.fetchone()[0]

            # Check for NULL or negative credits
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE credits IS NULL OR credits < 0")
            invalid_credits = self.cursor.fetchone()[0]

            integrity_report = {
                'premium_users': premium_count,
                'lifetime_users': lifetime_count,
                'corrupt_entries': corrupt_count,
                'missing_referral_codes': missing_referral_codes,
                'invalid_credits': invalid_credits,
                'integrity_ok': corrupt_count == 0 and missing_referral_codes == 0 and invalid_credits == 0
            }

            print(f"📊 Data Integrity: Premium={premium_count}, Lifetime={lifetime_count}, Corrupt={corrupt_count}")
            print(f"📊 Referral Integrity: Missing codes={missing_referral_codes}, Invalid credits={invalid_credits}")

            return integrity_report

        except Exception as e:
            print(f"❌ Error verifying data integrity: {e}")
            return {'integrity_ok': False, 'error': str(e)}

    def close(self):
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"Error closing database: {e}")