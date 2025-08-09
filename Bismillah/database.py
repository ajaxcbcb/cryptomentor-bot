# Adding the get_eligible_auto_signal_users method to the Database class.
import sqlite3
import os
from datetime import datetime, timedelta

class Database:
    """
    Manages all database operations for the CryptoMentor AI project.
    Handles user data, subscriptions, portfolios, and activity logging.
    """
    def __init__(self, db_path="cryptomentor.db"):
        """
        Initializes the database connection and creates tables if they don't exist.

        Args:
            db_path (str): The path to the SQLite database file.
        """
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise

    def create_tables(self):
        """
        Creates necessary database tables and ensures schema consistency.
        Includes logic for adding missing columns and emergency data recovery.
        """
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
        """
        Creates a new user in the database with enhanced persistence.
        Handles referral code generation and initial credit allocation.

        Args:
            telegram_id (int): The Telegram user ID.
            username (str): The Telegram username.
            first_name (str, optional): The user's first name. Defaults to None.
            last_name (str, optional): The user's last name. Defaults to None.
            language_code (str, optional): The user's language code. Defaults to 'id'.
            referred_by (int, optional): The Telegram ID of the referrer. Defaults to None.

        Returns:
            bool: True if the user was created successfully, False otherwise.
        """
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
        """
        Updates user information without affecting credits or premium status.

        Args:
            telegram_id (int): The Telegram user ID.
            username (str, optional): New username. Defaults to None.
            first_name (str, optional): New first name. Defaults to None.
            last_name (str, optional): New last name. Defaults to None.
            language_code (str, optional): New language code. Defaults to None.

        Returns:
            bool: True if update was successful, False otherwise.
        """
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
        """
        Adds a new user to the database, ignoring if the user already exists.

        Args:
            telegram_id (int): The Telegram user ID.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            username (str): The Telegram username.
            language_code (str, optional): The user's language code. Defaults to 'id'.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
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
        """
        Retrieves user information from the database by Telegram ID.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            dict or None: A dictionary containing user data if found, otherwise None.
        """
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
        """
        Updates a user's language preference in the database.

        Args:
            telegram_id (int): The Telegram user ID.
            language_code (str): The new language code.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
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
        """
        Checks if a user has an active premium subscription.
        Considers lifetime premium (subscription_end IS NULL) and checks for expiration.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            bool: True if the user is premium, False otherwise.
        """
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
        """
        Grants premium access to a user, either for a specific duration or permanently.

        Args:
            telegram_id (int): The Telegram user ID.
            granted_by_id (int): The Telegram ID of the granting admin.
            days (int, optional): The duration of premium access in days. 
                                  Use None for permanent access. Defaults to 30.

        Returns:
            bool: True if premium access was granted successfully, False otherwise.
        """
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
        """
        Revokes premium access from a user.

        Args:
            telegram_id (int): The Telegram user ID.
            revoked_by_id (int): The Telegram ID of the revoking admin (can be None).

        Returns:
            bool: True if premium access was revoked successfully, False otherwise.
        """
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
        """
        Retrieves a user's investment portfolio.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            list: A list of dictionaries, where each dictionary represents a portfolio item.
        """
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
        """
        Adds or updates an item in a user's portfolio. If the symbol already exists,
        it updates the amount and recalculates the average buy price.

        Args:
            telegram_id (int): The Telegram user ID.
            symbol (str): The cryptocurrency symbol (e.g., 'BTC').
            amount (float): The amount of the cryptocurrency.
            avg_buy_price (float): The average buy price for this amount.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
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
        """
        Logs user actions for auditing and debugging purposes.

        Args:
            user_id (int): The Telegram user ID.
            action (str): The type of action performed (e.g., 'command_used', 'signal_sent').
            details (str, optional): Additional details about the action. Defaults to None.

        Returns:
            bool: True if logging was successful, False otherwise.
        """
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
        """
        Logs the details of an automated signal broadcast for monitoring.

        Args:
            signals_count (int): The number of signals broadcasted.
            users_reached (int): The number of users who received the signals.
            total_eligible (int): The total number of users eligible for signals.

        Returns:
            bool: True if logging was successful, False otherwise.
        """
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
        """
        Retrieves basic user statistics (total, premium, free users).

        Returns:
            dict: A dictionary containing user statistics.
        """
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
        """
        Retrieves the current credit balance for a specific user.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            int: The user's credit balance, or 0 if the user is not found or an error occurs.
        """
        try:
            user = self.get_user(telegram_id)
            return user.get('credits', 0) if user else 0
        except Exception as e:
            print(f"Error getting user credits: {e}")
            return 0

    def get_eligible_auto_signal_users(self):
        """
        Retrieves a list of users eligible for automated signals.
        This includes all admin users and users with lifetime premium subscriptions.

        Returns:
            list: A list of dictionaries, each containing 'telegram_id', 'first_name', and 'type' 
                  ('adminX' or 'lifetime') for eligible users.
        """
        try:
            # Get all admin users from environment variables
            admin_ids = set()

            # Collect all admin IDs
            for i in range(1, 10):  # Support ADMIN_USER_ID to ADMIN9_USER_ID
                key = f'ADMIN_USER_ID' if i == 1 else f'ADMIN{i}_USER_ID'
                admin_id_str = os.getenv(key, '0')
                try:
                    admin_id = int(admin_id_str)
                    if admin_id > 0:
                        admin_ids.add(admin_id)
                except ValueError:
                    continue

            eligible_users = []

            # Add all admin users
            for idx, admin_id in enumerate(sorted(admin_ids), 1):
                admin_user = self.get_user(admin_id)
                if admin_user:
                    eligible_users.append({
                        'telegram_id': admin_id,
                        'first_name': admin_user.get('first_name', f'Admin{idx}'),
                        'type': f'admin{idx}'
                    })
                else:
                    print(f"⚠️ Admin{idx} user {admin_id} not found in database")

            # Get lifetime premium users (subscription_end IS NULL means lifetime)
            self.cursor.execute("""
                SELECT telegram_id, first_name FROM users 
                WHERE is_premium = 1 AND subscription_end IS NULL
            """)
            lifetime_users = self.cursor.fetchall()

            for user in lifetime_users:
                if user[0] not in admin_ids:  # Don't duplicate admin users
                    eligible_users.append({
                        'telegram_id': user[0],
                        'first_name': user[1] or 'User',
                        'type': 'lifetime'
                    })

            print(f"👥 Auto signals eligible: {len(admin_ids)} Admins + {len(lifetime_users)} Lifetime users")
            return eligible_users

        except Exception as e:
            print(f"❌ Error getting eligible auto signal users: {e}")
            return []

    def deduct_credit(self, telegram_id, amount):
        """
        Deducts credits from a user's account. This action is only performed
        for non-premium and non-admin users.

        Args:
            telegram_id (int): The Telegram user ID.
            amount (int): The number of credits to deduct.

        Returns:
            bool: True if credits were deducted successfully, False otherwise (e.g., insufficient credits, user is premium/admin).
        """
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
        """
        Retrieves overall bot statistics, including user counts and activity.

        Returns:
            dict: A dictionary containing bot statistics.
        """
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
        """
        Grants premium access to a user for a specified number of days.

        Args:
            telegram_id (int): The Telegram user ID.
            days (int, optional): The duration of premium access in days. Defaults to 30.

        Returns:
            bool: True if premium access was granted, False otherwise.
        """
        return self.grant_premium_access(telegram_id, None, days)

    def grant_permanent_premium(self, telegram_id):
        """
        Grants permanent premium access to a user.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            bool: True if permanent premium access was granted, False otherwise.
        """
        return self.grant_premium_access(telegram_id, None, None)

    def grant_premium_by_package(self, telegram_id, package_type):
        """
        Grants premium access based on a package type (e.g., '1_month', 'lifetime').

        Args:
            telegram_id (int): The Telegram user ID.
            package_type (str): The type of premium package.

        Returns:
            bool: True if premium access was granted according to the package, False otherwise.
        """
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
        """
        Revokes premium access from a user.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            bool: True if premium access was revoked, False otherwise.
        """
        return self.revoke_premium_access(telegram_id, None)

    def add_to_portfolio(self, telegram_id, symbol, amount, avg_buy_price=0):
        """
        Adds a cryptocurrency to a user's portfolio or updates it if it already exists.

        Args:
            telegram_id (int): The Telegram user ID.
            symbol (str): The cryptocurrency symbol (e.g., 'BTC').
            amount (float): The amount of the cryptocurrency.
            avg_buy_price (float, optional): The average buy price. Defaults to 0.

        Returns:
            bool: True if the portfolio item was added/updated successfully, False otherwise.
        """
        return self.add_portfolio_item(telegram_id, symbol, amount, avg_buy_price)

    def get_user_by_referral_code(self, referral_code):
        """
        Retrieves a user's Telegram ID based on their referral code.

        Args:
            referral_code (str): The referral code to look up.

        Returns:
            int or None: The user's Telegram ID if found, otherwise None. Returns 0 if not found.
        """
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
        """
        Updates a user's language preference.

        Args:
            telegram_id (int): The Telegram user ID.
            language (str): The new language code.

        Returns:
            bool: True if the language was updated successfully, False otherwise.
        """
        try:
            self.cursor.execute("""
                UPDATE users SET language_code = ? WHERE telegram_id = ?
            """, (language, telegram_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"DB Error (update_user_language): {e}")
            return False

    def get_bot_statistics(self):
        """
        Retrieves comprehensive bot usage statistics.

        Returns:
            dict: A dictionary containing various statistics like total users, active users, credits, etc.
        """
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
        """
        Retrieves the most recent user activity logs.

        Args:
            limit (int, optional): The maximum number of activities to retrieve. Defaults to 10.

        Returns:
            list: A list of dictionaries, each representing a user activity log entry.
        """
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
        """
        Revokes premium status from a specific user.

        Args:
            user_id (int): The Telegram user ID.

        Returns:
            bool: True if premium status was revoked, False otherwise.
        """
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
        """
        Fixes issues with user credits by setting NULL or negative credit balances to default values.

        Returns:
            int: The total number of users whose credits were fixed.
        """
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

    def mark_all_users_for_restart(self):
        """
        Marks all users as needing a restart by logging a 'restart_required' activity.

        Returns:
            int: The number of users marked for restart.
        """
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
        """
        Checks if a user needs to restart their session after a bot restart.
        This is determined by checking for a 'restart_required' flag that hasn't been cleared.

        Args:
            user_id (int): The Telegram user ID.

        Returns:
            bool: True if the user needs to restart, False otherwise.
        """
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
        """
        Clears the restart flag for a user. In this implementation, this is handled
        implicitly by the 'user_reactivated' log entry logic in `user_needs_restart`.

        Args:
            user_id (int): The Telegram user ID.

        Returns:
            bool: Always returns True as the operation is handled implicitly.
        """
        try:
            # This is handled by logging the reactivation
            return True
        except Exception as e:
            print(f"Error clearing restart flag for user {user_id}: {e}")
            return False

    def refresh_all_free_user_credits(self):
        """
        Grants a bonus of 50 credits to all users who are not premium.

        Returns:
            int: The number of free users who received bonus credits.
        """
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
        """
        Logs the results of an automated signals broadcast for performance monitoring.

        Args:
            signals_count (int): The total number of signals sent.
            success_count (int): The number of signals successfully delivered.
            total_eligible (int): The total number of users eligible to receive signals.

        Returns:
            bool: True if the broadcast log was created successfully, False otherwise.
        """
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
        """
        Retrieves a list of all users in the database, including their basic information.
        Useful for broadcast or administrative tasks.

        Returns:
            list: A list of dictionaries, each containing user ID, name, username, premium status, and creation date.
        """
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
        """
        Retrieves a user's Telegram ID based on their premium referral code.

        Args:
            premium_code (str): The premium referral code to look up.

        Returns:
            int or None: The user's Telegram ID if found, otherwise None.
        """
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
        """
        Retrieves both the free and premium referral codes for a given user.

        Args:
            telegram_id (int): The Telegram user ID.

        Returns:
            dict or None: A dictionary containing 'free_referral_code' and 'premium_referral_code',
                          or None if the user is not found.
        """
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
        """
        Retrieves statistics related to a user's premium referrals, including total
        successful referrals and earnings.

        Args:
            telegram_id (int): The Telegram user ID of the referrer.

        Returns:
            dict: A dictionary containing 'total_referrals', 'total_earnings', and 'recent_referrals'.
        """
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
        """
        Records a premium referral reward when a referred user subscribes to a premium plan.
        Updates the referrer's earnings and logs the reward.

        Args:
            referrer_id (int): The Telegram ID of the referrer.
            referred_id (int): The Telegram ID of the referred user.
            subscription_type (str): The type of subscription the referred user purchased.
            package_amount (int): The amount paid for the subscription package.

        Returns:
            bool: True if the reward was recorded successfully, False otherwise.
        """
        try:
            # Calculate earnings (Rp 10,000 per premium subscription)
            earnings = 10000

            self.cursor.execute("""
                INSERT INTO premium_referrals 
                (referrer_id, referred_id, subscription_type, subscription_amount, earnings, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'paid', datetime('now'))
            """, (referrer_id, referred_id, subscription_type, package_amount, earnings))

            # Update referrer's premium earnings
            self.cursor.execute("""
                UPDATE users SET premium_earnings = premium_earnings + ? WHERE telegram_id = ?
            """, (earnings, referrer_id))

            self.conn.commit()

            # Log the reward
            self.log_user_activity(referrer_id, "premium_referral_reward", 
                                 f"Earned Rp {earnings:,} from {referred_id} subscribing {subscription_type}")

            return True
        except Exception as e:
            print(f"Error recording premium referral reward: {e}")
            return False

    def check_premium_referral(self, telegram_id):
        """
        Checks if a user was initially referred via a premium referral link.

        Args:
            telegram_id (int): The Telegram user ID to check.

        Returns:
            int or None: The Telegram ID of the referrer if found, otherwise None.
        """
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
        """
        Adds credits to a user's account.

        Args:
            telegram_id (int): The Telegram user ID.
            amount (int): The number of credits to add.

        Returns:
            bool: True if credits were added successfully, False otherwise.
        """
        try:
            self.cursor.execute("""
                UPDATE users SET credits = credits + ? WHERE telegram_id = ?
            """, (amount, telegram_id))

            success = self.cursor.rowcount > 0
            if success:
                self.conn.commit()

            return success
        except Exception as e:
            print(f"DB Error (add_credits): {e}")
            return False

    def ensure_user_persistence(self, telegram_id, username, first_name, last_name, language_code):
        """
        Ensures a user's data is correctly persisted in the database, either by creating
        a new record or updating an existing one.

        Args:
            telegram_id (int): The Telegram user ID.
            username (str): The Telegram username.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            language_code (str): The user's language code.

        Returns:
            bool: True if user data was persisted successfully, False otherwise.
        """
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
        """
        Creates a backup log entry for a user's data. This is a simple logging mechanism
        and not a full database backup.

        Args:
            telegram_id (int): The Telegram user ID to back up.

        Returns:
            bool: True if the backup log was created, False otherwise.
        """
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
        """
        Placeholder function for user recovery from backup logs.
        Actual implementation would depend on the backup strategy.

        Args:
            telegram_id (int): The Telegram user ID to recover.

        Returns:
            bool: True if the recovery attempt was logged, False otherwise.
        """
        try:
            # This is a placeholder - implement based on your backup strategy
            self.log_user_activity(telegram_id, "recovery_attempted", f"Recovery attempted for user {telegram_id}")
            return True
        except Exception as e:
            print(f"Error recovering user from backup: {e}")
            return False

    def set_user_language(self, telegram_id, language):
        """
        Sets the language preference for a user.

        Args:
            telegram_id (int): The Telegram user ID.
            language (str): The new language code.

        Returns:
            bool: True if the language was set successfully, False otherwise.
        """
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
        """
        Creates automatic backups of critical database tables (users, premium_referrals).
        Backups are named with a timestamp.

        Returns:
            str or None: The timestamp string used for the backup if successful, otherwise None.
        """
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
        """
        Verifies the integrity of user data by checking for premium status, lifetime
        subscriptions, and potential data corruption (e.g., missing Telegram IDs).

        Returns:
            dict: A report containing integrity checks and an overall integrity status.
        """
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

            integrity_report = {
                'premium_users': premium_count,
                'lifetime_users': lifetime_count,
                'corrupt_entries': corrupt_count,
                'integrity_ok': corrupt_count == 0
            }

            print(f"📊 Data Integrity: Premium={premium_count}, Lifetime={lifetime_count}, Corrupt={corrupt_count}")
            return integrity_report

        except Exception as e:
            print(f"❌ Error verifying data integrity: {e}")
            return {'integrity_ok': False, 'error': str(e)}

    def close(self):
        """Closes the database connection."""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"Error closing database: {e}")