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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    banned INTEGER DEFAULT 0
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
                ('timezone', "TEXT DEFAULT 'WIB'"),
                ('is_premium', 'INTEGER DEFAULT 0'),
                ('credits', 'INTEGER DEFAULT 0'),
                ('subscription_end', 'TEXT'),
                ('referred_by', 'INTEGER'),
                ('referral_code', 'TEXT'),
                ('premium_referral_code', 'TEXT'),
                ('premium_earnings', 'INTEGER DEFAULT 0'),
                ('banned', 'INTEGER DEFAULT 0')
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
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            banned INTEGER DEFAULT 0
                        )
                    """)

                    # Restore ALL data preserving premium status
                    self.cursor.execute(f"""
                        INSERT INTO users (telegram_id, first_name, last_name, username, language_code, 
                                         is_premium, credits, subscription_end, referred_by, referral_code,
                                         premium_referral_code, premium_earnings, created_at, banned)
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
                               COALESCE(banned, 0)
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
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            banned INTEGER DEFAULT 0
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

    def _generate_free_referral_code(self, telegram_id):
        """Generates a unique free referral code."""
        import random
        import string
        attempts = 0
        while attempts < 10:
            code = 'F' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            if not self.get_user_by_referral_code(code):
                return code
            attempts += 1
        return f'F{telegram_id}{random.randint(1000,9999)}' # Fallback

    def _generate_premium_referral_code(self, telegram_id):
        """Generates a unique premium referral code."""
        import random
        import string
        attempts = 0
        while attempts < 10:
            code = 'P' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            if not self.get_user_by_premium_referral_code(code):
                return code
            attempts += 1
        return f'P{telegram_id}{random.randint(1000,9999)}' # Fallback

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Executes a query and handles fetching results."""
        try:
            self.cursor.execute(query, params or ())
            if fetch_one:
                row = self.cursor.fetchone()
                if row:
                    # Try to return as dictionary if column names are available
                    columns = [description[0] for description in self.cursor.description]
                    return dict(zip(columns, row))
                return None
            elif fetch_all:
                columns = [description[0] for description in self.cursor.description]
                return [dict(zip(columns, r)) for r in self.cursor.fetchall()]
            else:
                self.conn.commit()
                return self.cursor.rowcount # Indicate rows affected for INSERT/UPDATE/DELETE
        except Exception as e:
            print(f"DB Error executing query: {e}\nQuery: {query}\nParams: {params}")
            self.conn.rollback() # Rollback on error
            return None


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
            referral_code = self._generate_free_referral_code(telegram_id)
            premium_referral_code = self._generate_premium_referral_code(telegram_id)

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
                       is_premium, credits, subscription_end, referred_by, referral_code, 
                       created_at, banned, premium_earnings
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
                    'created_at': row[10],
                    'banned': row[11],
                    'premium_earnings': row[12] if len(row) > 12 else 0
                }
            return None
        except Exception as e:
            print(f"DB Error (get_user): {e}")
            return None

    def update_user_language(self, telegram_id, language_code):
        """Update user's language preference"""
        try:
            # Validate language code
            valid_languages = ['id', 'en'] # Add more languages as needed
            if language_code not in valid_languages:
                print(f"❌ Invalid language code: {language_code}")
                # Optionally, set to default or return False
                language_code = 'id' # Default to Indonesian if invalid

            self.cursor.execute("""
                UPDATE users SET language_code = ? WHERE telegram_id = ?
            """, (language_code, telegram_id))

            success = self.cursor.rowcount > 0
            if success:
                self.conn.commit()
                # Log language change
                self.log_user_activity(
                    telegram_id, 
                    "language_changed", 
                    f"Language changed to {language_code}"
                )
                print(f"✅ Updated language for user {telegram_id}: {language_code}")
            else:
                print(f"❌ User {telegram_id} not found when updating language")

            return success
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
            admin1_id = 1187119989  # Primary admin
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
            # Get all admin IDs from environment variables
            admin_ids = set()
            for i in range(1, 6): # Check up to ADMIN5_USER_ID
                key = f'ADMIN_USER_ID' if i == 1 else f'ADMIN{i}_USER_ID'
                admin_id_str = os.getenv(key, '0')
                try:
                    admin_id = int(admin_id_str)
                    if admin_id > 0:
                        admin_ids.add(admin_id)
                except ValueError:
                    continue # Ignore if not a valid integer

            if self.is_user_premium(telegram_id) or telegram_id in admin_ids:
                # Admins and premium users don't lose credits
                return True

            # Check current credits first to ensure user has enough
            current_user = self.get_user(telegram_id)
            if not current_user:
                print(f"❌ User {telegram_id} not found for credit deduction.")
                return False

            current_credits = current_user.get('credits', 0)
            if current_credits < amount:
                print(f"❌ Insufficient credits for user {telegram_id}: has {current_credits}, needs {amount}")
                return False

            # Use execute_query for transaction safety
            self.cursor.execute("BEGIN TRANSACTION")
            self.cursor.execute("""
                UPDATE users SET credits = credits - ? 
                WHERE telegram_id = ? AND credits >= ?
            """, (amount, telegram_id, amount))

            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                self.conn.commit()
                # Log credit deduction for tracking
                remaining_credits = current_credits - amount
                self.log_user_activity(telegram_id, "credit_deduction", f"Deducted {amount} credits, remaining: {remaining_credits}")
                return True
            else:
                self.conn.rollback()
                print(f"❌ Credit deduction failed for user {telegram_id} (rowcount 0).")
                return False
        except Exception as e:
            self.conn.rollback()
            print(f"DB Error (deduct_credit): {e}")
            return False

    def get_bot_stats(self):
        """Get bot usage statistics"""
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

            # Banned users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
            banned_users = self.cursor.fetchone()[0]

            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'active_today': active_today,
                'banned_users': banned_users
            }
        except Exception as e:
            print(f"DB Error (get_bot_stats): {e}")
            return {'total_users': 0, 'premium_users': 0, 'active_today': 0, 'banned_users': 0}

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

            # Banned users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
            banned_users = self.cursor.fetchone()[0]

            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'active_today': active_today,
                'total_credits': total_credits,
                'commands_today': commands_today,
                'avg_credits': avg_credits,
                'analyses_count': analyses_count,
                'banned_users': banned_users
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
                'analyses_count': 0,
                'banned_users': 0
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
        """Fix NULL and negative credits for all users"""
        try:
            # Fix NULL credits - set to 100
            self.cursor.execute("""
                UPDATE users 
                SET credits = 100 
                WHERE credits IS NULL AND (is_premium = 0 OR is_premium IS NULL)
            """)
            null_fixed = self.cursor.rowcount

            # Fix negative credits - set to 10
            self.cursor.execute("""
                UPDATE users 
                SET credits = 10 
                WHERE credits < 0 AND (is_premium = 0 OR is_premium IS NULL)
            """)
            negative_fixed = self.cursor.rowcount

            self.conn.commit()
            total_fixed = null_fixed + negative_fixed

            print(f"✅ Fixed credits for {total_fixed} users (NULL: {null_fixed}, Negative: {negative_fixed})")
            return total_fixed

        except Exception as e:
            print(f"❌ Error fixing user credits: {e}")
            self.conn.rollback()
            return 0

    def set_all_user_credits(self, amount):
        """Set specific credit amount for all non-premium users"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET credits = ? 
                WHERE (is_premium = 0 OR is_premium IS NULL)
            """, (amount,))

            updated_count = self.cursor.rowcount
            self.conn.commit()

            print(f"✅ Set {amount} credits for {updated_count} free users")
            return updated_count

        except Exception as e:
            print(f"❌ Error setting user credits: {e}")
            self.conn.rollback()
            return 0

    def reset_credits_below_threshold(self, threshold=100, new_amount=100):
        """Reset credits ONLY for users below a certain threshold"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET credits = ? 
                WHERE credits < ? 
                AND (is_premium = 0 OR is_premium IS NULL)
            """, (new_amount, threshold))

            updated_count = self.cursor.rowcount
            self.conn.commit()

            print(f"✅ Reset {updated_count} users with credits < {threshold} to {new_amount}")
            return updated_count

        except Exception as e:
            print(f"❌ Error resetting credits below threshold: {e}")
            self.conn.rollback()
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
                    referral_code = self._generate_free_referral_code(telegram_id)

                # Generate premium referral code if missing
                if not premium_referral_code:
                    premium_referral_code = self._generate_premium_referral_code(telegram_id)

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
        """Give bonus credits to all free users"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET credits = credits + 50 
                WHERE is_premium = 0
            """)

            refreshed_count = self.cursor.rowcount
            self.conn.commit()

            print(f"✅ Gave +50 credits to {refreshed_count} free users")
            return refreshed_count
        except Exception as e:
            print(f"Error refreshing free user credits: {e}")
            return 0

    def log_auto_signals_broadcast(self, signals_count, success_count, total_eligible):
        """Log auto signals broadcast for tracking"""
        try:
            # Get first available admin ID for logging
            admin_id = 0
            for i in range(1, 6): # Check up to ADMIN5_USER_ID
                key = f'ADMIN_USER_ID' if i == 1 else f'ADMIN{i}_USER_ID'
                admin_id_str = os.getenv(key, '0')
                try:
                    potential_admin_id = int(admin_id_str)
                    if potential_admin_id > 0:
                        admin_id = potential_admin_id
                        break
                except ValueError:
                    continue # Ignore if not a valid integer

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
        """Get all users for broadcast functionality - Enhanced version"""
        try:
            # Enhanced query with proper filtering
            self.cursor.execute("""
                SELECT telegram_id, first_name, username, is_premium, created_at, banned
                FROM users 
                WHERE telegram_id IS NOT NULL 
                AND telegram_id != 0
                AND telegram_id != ''
                AND (banned IS NULL OR banned = 0)
                ORDER BY created_at DESC
            """)

            results = []
            seen_ids = set()
            
            for row in self.cursor.fetchall():
                telegram_id = row[0]
                
                # Skip duplicates and invalid IDs
                if telegram_id and telegram_id not in seen_ids:
                    try:
                        tid = int(telegram_id)
                        if tid > 0:  # Valid Telegram ID
                            seen_ids.add(telegram_id)
                            results.append({
                                'telegram_id': tid,
                                'user_id': tid,  # Alias for compatibility
                                'first_name': row[1],
                                'username': row[2],
                                'is_premium': row[3],
                                'created_at': row[4]
                            })
                    except (ValueError, TypeError):
                        # Skip invalid telegram_id
                        continue
            
            print(f"✅ Local DB: Found {len(results)} valid users")
            return results
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    def get_all_broadcast_users(self):
        """
        Get all users from both local and Supabase for broadcast
        Returns: dict with 'local', 'supabase', 'unique_ids', and stats
        """
        print("[get_all_broadcast_users] Starting...")
        
        result = {
            'local_users': [],
            'supabase_users': [],
            'unique_ids': set(),
            'stats': {
                'local_count': 0,
                'supabase_count': 0,
                'supabase_unique': 0,
                'total_unique': 0,
                'duplicates': 0
            }
        }
        
        try:
            # Get local users
            print("[get_all_broadcast_users] Fetching local users...")
            local_users = self.get_all_users()
            result['local_users'] = local_users
            
            for user in local_users:
                tid = user.get('telegram_id') or user.get('user_id')
                if tid and tid > 0:
                    result['unique_ids'].add(int(tid))
            
            result['stats']['local_count'] = len(local_users)
            print(f"[get_all_broadcast_users] Local users: {result['stats']['local_count']}")
            
            # Get Supabase users if available
            print(f"[get_all_broadcast_users] Supabase enabled: {self.supabase_enabled}")
            if self.supabase_enabled:
                try:
                    from supabase_client import supabase
                    if supabase:
                        # Enhanced query with filtering - check if banned column exists
                        # IMPORTANT: Supabase has default limit of 1000 rows
                        # We need to paginate to get ALL users
                        all_supabase_users = []
                        page_size = 1000
                        offset = 0
                        has_banned_column = True
                        
                        while True:
                            try:
                                # Try with banned column first
                                supabase_result = supabase.table('users')\
                                    .select('telegram_id, first_name, username, is_premium, banned')\
                                    .not_.is_('telegram_id', 'null')\
                                    .neq('telegram_id', 0)\
                                    .range(offset, offset + page_size - 1)\
                                    .execute()
                            except Exception as e:
                                # If banned column doesn't exist, query without it
                                if 'banned does not exist' in str(e) or '42703' in str(e):
                                    print("ℹ️  Supabase table doesn't have 'banned' column, querying without it")
                                    has_banned_column = False
                                    supabase_result = supabase.table('users')\
                                        .select('telegram_id, first_name, username, is_premium')\
                                        .not_.is_('telegram_id', 'null')\
                                        .neq('telegram_id', 0)\
                                        .range(offset, offset + page_size - 1)\
                                        .execute()
                                else:
                                    raise e
                            
                            if not supabase_result.data:
                                break  # No more data
                            
                            all_supabase_users.extend(supabase_result.data)
                            
                            # If we got less than page_size, we've reached the end
                            if len(supabase_result.data) < page_size:
                                break
                            
                            offset += page_size
                            print(f"📄 Fetched {len(all_supabase_users)} users from Supabase so far...")
                        
                        supabase_result.data = all_supabase_users
                        print(f"✅ Total Supabase users fetched: {len(all_supabase_users)}")
                        
                        if supabase_result.data:
                            supabase_unique = 0
                            for user in supabase_result.data:
                                tid = user.get('telegram_id')
                                is_banned = user.get('banned', 0) if has_banned_column else 0
                                
                                # Skip banned and invalid
                                if tid and tid > 0 and not is_banned:
                                    result['supabase_users'].append(user)
                                    result['stats']['supabase_count'] += 1
                                    
                                    if tid not in result['unique_ids']:
                                        supabase_unique += 1
                                        result['unique_ids'].add(int(tid))
                            
                            result['stats']['supabase_unique'] = supabase_unique
                        
                        print(f"✅ Supabase: Found {result['stats']['supabase_count']} valid users, {result['stats']['supabase_unique']} unique")
                except Exception as e:
                    print(f"⚠️ Supabase fetch error in get_all_broadcast_users: {e}")
            
            # Calculate final stats
            result['stats']['total_unique'] = len(result['unique_ids'])
            result['stats']['duplicates'] = (result['stats']['local_count'] + 
                                            result['stats']['supabase_count'] - 
                                            result['stats']['total_unique'])
            
            print(f"📊 Broadcast Stats: {result['stats']['local_count']} local, "
                  f"{result['stats']['supabase_count']} supabase, "
                  f"{result['stats']['total_unique']} unique, "
                  f"{result['stats']['duplicates']} duplicates")
            
            return result
            
        except Exception as e:
            print(f"Error in get_all_broadcast_users: {e}")
            return result

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
        """Record premium referral reward when someone subscribes - uses enhanced tier system"""
        return self.record_enhanced_premium_referral_reward(referrer_id, referred_id, subscription_type, package_amount)

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

            # Check for banned users
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
            banned_users_count = self.cursor.fetchone()[0]

            integrity_report = {
                'premium_users': premium_count,
                'lifetime_users': lifetime_count,
                'corrupt_entries': corrupt_count,
                'missing_referral_codes': missing_referral_codes,
                'invalid_credits': invalid_credits,
                'banned_users': banned_users_count,
                'integrity_ok': corrupt_count == 0 and missing_referral_codes == 0 and invalid_credits == 0
            }

            print(f"📊 Data Integrity: Premium={premium_count}, Lifetime={lifetime_count}, Corrupt={corrupt_count}")
            print(f"📊 Referral Integrity: Missing codes={missing_referral_codes}, Invalid credits={invalid_credits}, Banned={banned_users_count}")

            return integrity_report

        except Exception as e:
            print(f"❌ Error verifying data integrity: {e}")
            return {'integrity_ok': False, 'error': str(e)}

    def ban_user(self, telegram_id):
        """Ban a user from using the bot"""
        try:
            self.cursor.execute("""
                UPDATE users SET banned = 1 
                WHERE telegram_id = ?
            """, (telegram_id,))
            self.conn.commit()

            # Log the ban action
            self.log_user_activity(telegram_id, "user_banned", "User has been banned by admin")

            print(f"✅ User {telegram_id} has been banned")
            return True
        except Exception as e:
            print(f"❌ Error banning user {telegram_id}: {e}")
            return False

    def unban_user(self, telegram_id):
        """Unban a user, allowing them to use the bot again"""
        try:
            self.cursor.execute("""
                UPDATE users SET banned = 0 
                WHERE telegram_id = ?
            """, (telegram_id,))
            self.conn.commit()

            # Log the unban action
            self.log_user_activity(telegram_id, "user_unbanned", "User has been unbanned by admin")

            print(f"✅ User {telegram_id} has been unbanned")
            return True
        except Exception as e:
            print(f"❌ Error unbanning user {telegram_id}: {e}")
            return False

    def is_user_banned(self, telegram_id):
        """Check if a user is banned"""
        try:
            self.cursor.execute("""
                SELECT banned FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            result = self.cursor.fetchone()
            return bool(result[0]) if result else False
        except Exception as e:
            print(f"❌ Error checking ban status for user {telegram_id}: {e}")
            return False

    def get_detailed_referral_stats(self, telegram_id):
        """Get detailed referral statistics for a user"""
        try:
            from datetime import datetime, timedelta

            # Get total referrals
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE referred_by = ?
            """, (telegram_id,))
            total_referrals = self.cursor.fetchone()[0]

            # Get active referrals (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            self.cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE referred_by = ? AND created_at >= ?
            """, (telegram_id, thirty_days_ago))
            active_referrals = self.cursor.fetchone()[0]

            # Get total earnings from premium referrals
            self.cursor.execute("""
                SELECT COALESCE(SUM(earnings), 0) FROM premium_referrals 
                WHERE referrer_id = ? AND status = 'paid'
            """, (telegram_id,))
            total_earnings = self.cursor.fetchone()[0]

            # Get this month's earnings
            current_month = datetime.now().strftime('%Y-%m')
            self.cursor.execute("""
                SELECT COALESCE(SUM(earnings), 0) FROM premium_referrals 
                WHERE referrer_id = ? AND status = 'paid' 
                AND strftime('%Y-%m', created_at) = ?
            """, (telegram_id, current_month))
            this_month_earnings = self.cursor.fetchone()[0]

            return {
                'total_referrals': total_referrals or 0,
                'active_referrals': active_referrals or 0,
                'total_earnings': total_earnings or 0,
                'this_month_earnings': this_month_earnings or 0
            }
        except Exception as e:
            print(f"Error getting detailed referral stats: {e}")
            return {
                'total_referrals': 0,
                'active_referrals': 0,
                'total_earnings': 0,
                'this_month_earnings': 0
            }

    def get_referral_stats(self, telegram_id):
        """Get basic referral statistics for a user"""
        try:
            # Get total referrals
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE referred_by = ?
            """, (telegram_id,))
            total_referrals = self.cursor.fetchone()[0]

            # Get premium earnings
            self.cursor.execute("""
                SELECT COALESCE(premium_earnings, 0) FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            result = self.cursor.fetchone()
            total_earnings = result[0] if result else 0

            return {
                'total_referrals': total_referrals or 0,
                'total_earnings': total_earnings or 0
            }
        except Exception as e:
            print(f"Error getting referral stats: {e}")
            return {'total_referrals': 0, 'total_earnings': 0}

    def get_user_language(self, telegram_id):
        """Get user's language preference"""
        try:
            user = self.get_user(telegram_id)
            if user and user.get('language_code'):
                return user.get('language_code')
            else:
                # Default to Indonesian and update user if exists
                if user:
                    self.update_user_language(telegram_id, 'id')
                return 'id'
        except Exception as e:
            print(f"Error getting user language: {e}")
            return 'id' # Default language

    def get_user_timezone(self, telegram_id):
        """Get user's timezone preference"""
        try:
            user = self.get_user(telegram_id)
            return user.get('timezone', 'WIB') if user else 'WIB'
        except Exception as e:
            print(f"Error getting user timezone: {e}")
            return 'WIB'

    def set_user_timezone(self, telegram_id, timezone):
        """Set user's timezone preference"""
        try:
            self.cursor.execute("UPDATE users SET timezone = ? WHERE telegram_id = ?", (timezone, telegram_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error setting user timezone: {e}")
            return False

    def get_all_referrals(self, telegram_id):
        """Get all users referred by this user"""
        try:
            self.cursor.execute("""
                SELECT telegram_id, first_name, username, is_premium, created_at
                FROM users 
                WHERE referred_by = ?
                ORDER BY created_at DESC
            """, (telegram_id,))

            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'telegram_id': row[0],
                    'first_name': row[1],
                    'username': row[2],
                    'is_premium': row[3],
                    'created_at': row[4]
                })
            return results
        except Exception as e:
            print(f"Error getting all referrals: {e}")
            return []

    def get_referral_earnings_summary(self, telegram_id):
        """Get detailed earnings summary for referrals"""
        try:
            # Get premium referral earnings
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_premium_referrals,
                    COALESCE(SUM(earnings), 0) as total_premium_earnings
                FROM premium_referrals 
                WHERE referrer_id = ? AND status = 'paid'
            """, (telegram_id,))

            premium_result = self.cursor.fetchone()
            premium_referrals = premium_result[0] if premium_result else 0
            premium_earnings = premium_result[1] if premium_result else 0

            # Get free referral count
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE referred_by = ?
            """, (telegram_id,))
            total_referrals = self.cursor.fetchone()[0] or 0
            free_referrals = total_referrals - premium_referrals

            # Calculate credit earnings (5 credits per free referral)
            credit_earnings = free_referrals * 5

            return {
                'total_referrals': total_referrals,
                'free_referrals': free_referrals,
                'premium_referrals': premium_referrals,
                'credit_earnings': credit_earnings,
                'money_earnings': premium_earnings,
                'total_value': premium_earnings + (credit_earnings * 100)  # Estimate credit value
            }
        except Exception as e:
            print(f"Error getting referral earnings summary: {e}")
            return {
                'total_referrals': 0,
                'free_referrals': 0,
                'premium_referrals': 0,
                'credit_earnings': 0,
                'money_earnings': 0,
                'total_value': 0
            }

    def process_referral_reward(self, referrer_id, referred_id):
        """Process referral reward when someone joins - uses enhanced tier system"""
        return self.process_enhanced_referral_reward(referrer_id, referred_id)

    def get_user_tier(self, telegram_id):
        """Get user's referral tier based on total referrals with enhanced system"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE referred_by = ?
            """, (telegram_id,))
            total_referrals = self.cursor.fetchone()[0] or 0

            if total_referrals >= 100:
                return {'tier': 'DIAMOND', 'level': 5, 'bonus': 30, 'money_multiplier': 3.0}
            elif total_referrals >= 50:
                return {'tier': 'GOLD', 'level': 4, 'bonus': 20, 'money_multiplier': 2.5}
            elif total_referrals >= 25:
                return {'tier': 'SILVER', 'level': 3, 'bonus': 15, 'money_multiplier': 2.0}
            elif total_referrals >= 10:
                return {'tier': 'BRONZE', 'level': 2, 'bonus': 10, 'money_multiplier': 1.5}
            else:
                return {'tier': 'STARTER', 'level': 1, 'bonus': 5, 'money_multiplier': 1.0}
        except Exception as e:
            print(f"Error getting user tier: {e}")
            return {'tier': 'STARTER', 'level': 1, 'bonus': 5, 'money_multiplier': 1.0}

    def apply_tier_bonus_to_credits(self, telegram_id, base_credits):
        """Apply tier bonus to credit rewards"""
        try:
            tier = self.get_user_tier(telegram_id)
            bonus_percentage = tier['bonus']
            bonus_credits = int(base_credits * (bonus_percentage / 100))
            total_credits = base_credits + bonus_credits

            return {
                'base_credits': base_credits,
                'bonus_credits': bonus_credits, 
                'total_credits': total_credits,
                'tier': tier['tier'],
                'bonus_percentage': bonus_percentage
            }
        except Exception as e:
            print(f"Error applying tier bonus: {e}")
            return {
                'base_credits': base_credits,
                'bonus_credits': 0,
                'total_credits': base_credits,
                'tier': 'STARTER',
                'bonus_percentage': 0
            }

    def apply_tier_multiplier_to_earnings(self, telegram_id, base_earnings):
        """Apply tier multiplier to money earnings"""
        try:
            tier = self.get_user_tier(telegram_id)
            multiplier = tier['money_multiplier']
            total_earnings = int(base_earnings * multiplier)
            bonus_earnings = total_earnings - base_earnings

            return {
                'base_earnings': base_earnings,
                'bonus_earnings': bonus_earnings,
                'total_earnings': total_earnings,
                'tier': tier['tier'],
                'multiplier': multiplier
            }
        except Exception as e:
            print(f"Error applying tier multiplier: {e}")
            return {
                'base_earnings': base_earnings,
                'bonus_earnings': 0,
                'total_earnings': base_earnings,
                'tier': 'STARTER',
                'multiplier': 1.0
            }

    def process_enhanced_referral_reward(self, referrer_id, referred_id):
        """Process referral reward with tier system bonuses"""
        try:
            base_credits = 5

            # Apply tier bonus
            credit_result = self.apply_tier_bonus_to_credits(referrer_id, base_credits)
            total_credits = credit_result['total_credits']

            # Add credits to referrer
            self.cursor.execute("""
                UPDATE users SET credits = credits + ? WHERE telegram_id = ?
            """, (total_credits, referrer_id))

            if self.cursor.rowcount > 0:
                self.conn.commit()
                # Log enhanced referral reward
                self.log_user_activity(
                    referrer_id, 
                    "enhanced_referral_reward", 
                    f"Earned {total_credits} credits ({base_credits} base + {credit_result['bonus_credits']} {credit_result['tier']} bonus) from referral {referred_id}"
                )
                print(f"✅ Enhanced referral reward processed: {referrer_id} got {total_credits} credits ({credit_result['tier']} tier)")
                return True
            return False
        except Exception as e:
            print(f"Error processing enhanced referral reward: {e}")
            return False

    def record_enhanced_premium_referral_reward(self, referrer_id, referred_id, subscription_type, package_amount):
        """Record premium referral reward with tier multipliers"""
        try:
            if not referrer_id or not referred_id:
                return False

            referrer = self.get_user(referrer_id)
            # Check if referrer exists and is premium
            if not referrer or not self.is_user_premium(referrer_id):
                print(f"Skipping premium referral reward for {referrer_id}: Referrer not found or not premium.")
                return False

            base_earnings = 10000  # Base Rp 10,000

            # Apply tier multiplier
            earnings_result = self.apply_tier_multiplier_to_earnings(referrer_id, base_earnings)
            total_earnings = earnings_result['total_earnings']

            # Record the enhanced premium referral
            self.cursor.execute("""
                INSERT INTO premium_referrals 
                (referrer_id, referred_id, subscription_type, subscription_amount, earnings, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'paid', datetime('now'))
            """, (referrer_id, referred_id, subscription_type, package_amount, total_earnings))

            # Update referrer's premium earnings
            self.cursor.execute("""
                UPDATE users SET premium_earnings = COALESCE(premium_earnings, 0) + ? WHERE telegram_id = ?
            """, (total_earnings, referrer_id))

            self.conn.commit()

            # Log the enhanced reward
            self.log_user_activity(referrer_id, "enhanced_premium_referral_reward", 
                                 f"Earned Rp {total_earnings:,} ({base_earnings:,} base × {earnings_result['multiplier']}x {earnings_result['tier']} multiplier) from {referred_id} subscribing {subscription_type}")

            print(f"✅ Enhanced premium referral reward: {referrer_id} earned Rp {total_earnings:,} ({earnings_result['tier']} tier)")
            return True
        except Exception as e:
            print(f"Error recording enhanced premium referral reward: {e}")
            return False

    def get_tier_leaderboard(self, limit=20):
        """Get referral leaderboard with tier information"""
        try:
            self.cursor.execute("""
                SELECT 
                    u.telegram_id,
                    u.first_name,
                    u.username,
                    COUNT(r.telegram_id) as referral_count,
                    COALESCE(u.premium_earnings, 0) as earnings
                FROM users u
                LEFT JOIN users r ON r.referred_by = u.telegram_id
                WHERE u.telegram_id IS NOT NULL
                GROUP BY u.telegram_id, u.first_name, u.username, u.premium_earnings
                HAVING referral_count > 0
                ORDER BY referral_count DESC, earnings DESC
                LIMIT ?
            """, (limit,))

            results = []
            for i, row in enumerate(self.cursor.fetchall()):
                tier_info = self.get_user_tier(row[0])
                results.append({
                    'rank': i + 1,
                    'telegram_id': row[0],
                    'first_name': row[1],
                    'username': row[2],
                    'referral_count': row[3],
                    'earnings': row[4],
                    'tier': tier_info['tier'],
                    'tier_level': tier_info['level']
                })
            return results
        except Exception as e:
            print(f"Error getting tier leaderboard: {e}")
            return []

    def get_referral_milestones(self, telegram_id):
        """Get referral milestones and rewards"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE referred_by = ?
            """, (telegram_id,))
            total_referrals = self.cursor.fetchone()[0] or 0

            milestones = [
                {'count': 1, 'reward': '🎁 Welcome bonus: 20 credits', 'unlocked': total_referrals >= 1},
                {'count': 5, 'reward': '🎁 Bronze achiever: 50 bonus credits', 'unlocked': total_referrals >= 5},
                {'count': 10, 'reward': '🎁 Bronze tier: Community access + 10% bonus', 'unlocked': total_referrals >= 10},
                {'count': 15, 'reward': '🎁 Growth bonus: 100 credits + badge', 'unlocked': total_referrals >= 15},
                {'count': 25, 'reward': '🎁 Silver tier: 15% bonus + early access', 'unlocked': total_referrals >= 25},
                {'count': 35, 'reward': '🎁 Silver master: 1 week premium trial', 'unlocked': total_referrals >= 35},
                {'count': 50, 'reward': '🎁 Gold tier: VIP access + 20% bonus', 'unlocked': total_referrals >= 50},
                {'count': 75, 'reward': '🎁 Gold master: 1 month premium', 'unlocked': total_referrals >= 75},
                {'count': 100, 'reward': '🎁 Diamond tier: Elite access + 30% bonus', 'unlocked': total_referrals >= 100}
            ]

            return {
                'current_referrals': total_referrals,
                'milestones': milestones,
                'next_milestone': next((m for m in milestones if not m['unlocked']), None)
            }
        except Exception as e:
            print(f"Error getting referral milestones: {e}")
            return {'current_referrals': 0, 'milestones': [], 'next_milestone': None}

    def get_language_stats(self):
        """Get language usage statistics"""
        try:
            self.cursor.execute("""
                SELECT 
                    language_code, 
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL), 2) as percentage
                FROM users 
                WHERE telegram_id IS NOT NULL
                GROUP BY language_code
                ORDER BY count DESC
            """)

            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'language': row[0] or 'id',
                    'count': row[1],
                    'percentage': row[2]
                })
            return results
        except Exception as e:
            print(f"Error getting language stats: {e}")
            return []

    def batch_update_language(self, language_from, language_to):
        """Batch update user language preferences"""
        try:
            self.cursor.execute("""
                UPDATE users SET language_code = ? WHERE language_code = ?
            """, (language_to, language_from))

            updated_count = self.cursor.rowcount
            self.conn.commit()

            print(f"✅ Updated language for {updated_count} users: {language_from} → {language_to}")
            return updated_count
        except Exception as e:
            print(f"Error batch updating language: {e}")
            return 0

    def get_referral_leaderboard(self, limit=10):
        """Get top referrers leaderboard"""
        try:
            self.cursor.execute("""
                SELECT 
                    u.telegram_id,
                    u.first_name,
                    u.username,
                    COUNT(r.telegram_id) as referral_count,
                    COALESCE(u.premium_earnings, 0) as earnings
                FROM users u
                LEFT JOIN users r ON r.referred_by = u.telegram_id
                WHERE u.telegram_id IS NOT NULL
                GROUP BY u.telegram_id, u.first_name, u.username, u.premium_earnings
                HAVING referral_count > 0
                ORDER BY referral_count DESC, earnings DESC
                LIMIT ?
            """, (limit,))

            results = []
            for i, row in enumerate(self.cursor.fetchall()):
                results.append({
                    'rank': i + 1,
                    'telegram_id': row[0],
                    'first_name': row[1],
                    'username': row[2],
                    'referral_count': row[3],
                    'earnings': row[4]
                })
            return results
        except Exception as e:
            print(f"Error getting referral leaderboard: {e}")
            return []

    def close(self):
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"Error closing database: {e}")
    def add_user_premium(self, user_id, premium_until):
        """Add premium access to user"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET subscription_end = ?, is_premium = 1
                WHERE telegram_id = ?
            """, (premium_until, user_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error adding premium: {e}")
            return False

    def remove_user_premium(self, user_id):
        """Remove premium access from user"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET subscription_end = NULL, is_premium = 0
                WHERE telegram_id = ?
            """, (user_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing premium: {e}")
            return False

    def set_user_lifetime(self, user_id, is_lifetime=True):
        """Set user as lifetime premium"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET is_premium = 1, subscription_end = NULL
                WHERE telegram_id = ?
            """, (user_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error setting lifetime: {e}")
            return False

    def add_user_credits(self, user_id, amount):
        """Add credits to user"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET credits = COALESCE(credits, 0) + ?
                WHERE telegram_id = ?
            """, (amount, user_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error adding credits: {e}")
            return False

    def get_recent_users(self, limit=10):
        """Get recent users"""
        try:
            self.cursor.execute("""
                SELECT * FROM users 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            users = []
            for row in self.cursor.fetchall():
                user_dict = dict(zip(columns, row))
                users.append(user_dict)
            return users
        except Exception as e:
            print(f"Error getting recent users: {e}")
            return []

    def search_user(self, query):
        """Search user by ID or username"""
        try:
            # Try to parse as integer first (user ID)
            try:
                user_id = int(query)
                self.cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
            except ValueError:
                # Search by username
                self.cursor.execute("SELECT * FROM users WHERE username = ?", (query,))
            
            row = self.cursor.fetchone()
            if row:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error searching user: {e}")
            return None

    def ban_user(self, user_id):
        """Ban a user"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET banned = 1
                WHERE telegram_id = ?
            """, (user_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error banning user: {e}")
            return False

    def unban_user(self, user_id):
        """Unban a user"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET banned = 0
                WHERE telegram_id = ?
            """, (user_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error unbanning user: {e}")
            return False

    def get_all_users(self):
        """Get all users"""
        try:
            self.cursor.execute("SELECT * FROM users")
            columns = [description[0] for description in self.cursor.description]
            users = []
            for row in self.cursor.fetchall():
                user_dict = dict(zip(columns, row))
                users.append(user_dict)
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    def has_automaton_access(self, telegram_id):
        """Check if user has paid for Automaton access"""
        try:
            self.cursor.execute("""
                SELECT automaton_access FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = self.cursor.fetchone()
            if row:
                return bool(row[0])
            return False
        except Exception as e:
            print(f"DB Error (has_automaton_access): {e}")
            return False
    
    def grant_automaton_access(self, telegram_id):
        """Grant Automaton access to a user (after payment)"""
        try:
            self.cursor.execute("""
                UPDATE users SET automaton_access = 1 WHERE telegram_id = ?
            """, (telegram_id,))
            self.conn.commit()
            
            # Log the access grant
            self.log_user_activity(
                telegram_id,
                'automaton_access_granted',
                'Automaton access granted (Rp2,000,000 payment)'
            )
            
            print(f"✅ Granted Automaton access to user {telegram_id}")
            return True
        except Exception as e:
            print(f"DB Error (grant_automaton_access): {e}")
            return False
