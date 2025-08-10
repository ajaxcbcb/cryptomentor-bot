
import os
import json
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

class AdminAgent:
    """AI Agent untuk menjalankan command admin secara aman"""
    
    def __init__(self):
        self.supabase = None
        self.connection_status = {"validated": False, "error": None}
        self._validate_and_init_supabase()
    
    def _validate_and_init_supabase(self) -> bool:
        """Validasi konfigurasi dan inisialisasi koneksi Supabase"""
        try:
            # 1. Validasi environment variables
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not supabase_key:
                self.connection_status = {
                    "validated": False,
                    "error": {
                        "status": "error",
                        "code": "CONFIG_MISSING", 
                        "message": "Supabase belum dikonfigurasi. Set SUPABASE_URL & SUPABASE_SERVICE_ROLE_KEY."
                    }
                }
                return False
            
            # 2. Validasi format URL
            if not supabase_url.startswith("https://") or ".supabase.co" not in supabase_url:
                self.connection_status = {
                    "validated": False,
                    "error": {
                        "status": "error",
                        "code": "CONFIG_MISSING",
                        "message": "Format SUPABASE_URL tidak valid. Harus: https://<project-id>.supabase.co"
                    }
                }
                return False
            
            # 3. Inisialisasi client
            self.supabase = create_client(supabase_url, supabase_key)
            
            # 4. Test koneksi minimal
            result = self.supabase.table('users').select('id').limit(1).execute()
            
            # 5. Validasi kolom credits
            columns_check = self.supabase.table('users').select('id, credits, is_premium, premium_until').limit(1).execute()
            
            self.connection_status = {
                "validated": True,
                "error": None
            }
            return True
            
        except Exception as e:
            error_str = str(e)
            if "column" in error_str.lower() and "credits" in error_str.lower():
                error_code = "MISSING_COLUMN"
                error_msg = "Kolom 'credits' tidak ditemukan di public.users."
            elif "relation" in error_str.lower() and "users" in error_str.lower():
                error_code = "CONNECTION_FAILED"
                error_msg = "Tabel 'users' tidak ditemukan."
            else:
                error_code = "CONNECTION_FAILED"
                error_msg = "Gagal konek ke Supabase."
            
            self.connection_status = {
                "validated": False,
                "error": {
                    "status": "error",
                    "code": error_code,
                    "message": error_msg
                }
            }
            return False
    
    def get_connection_status(self):
        """Get status koneksi untuk diagnostik"""
        if self.connection_status["validated"]:
            return {
                "status": "success",
                "message": "Supabase connection validated successfully"
            }
        else:
            return self.connection_status["error"]
    
    def execute_command(self, command, *args):
        """Execute admin command dengan validasi"""
        # Check connection first
        if not self.connection_status["validated"]:
            return self.connection_status["error"]
        
        try:
            if command == "/setpremium":
                return self._set_premium(*args)
            elif command == "/revoke_premium":
                return self._revoke_premium(*args)
            elif command == "/grant_credits":
                return self._grant_credits(*args)
            elif command == "/check_user_status":
                return self._check_user_status(*args)
            else:
                return {
                    "status": "error",
                    "code": "COMMAND_UNKNOWN",
                    "message": f"Command {command} tidak dikenali"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "code": "DB_ERROR", 
                "message": f"Database error: {str(e)[:100]}"
            }
    
    def _validate_user_id(self, user_id_str):
        """Validasi user_id parameter"""
        try:
            user_id = int(user_id_str)
            return user_id
        except ValueError:
            return None
    
    def _parse_duration(self, duration_str):
        """Parse duration string ke timedelta atau None untuk lifetime"""
        duration_lower = duration_str.lower()
        
        if duration_lower in ["lifetime"]:
            return None  # Lifetime
        elif duration_lower in ["month", "months", "bulan"]:
            return timedelta(days=30)
        elif duration_lower.endswith("d"):
            try:
                days = int(duration_lower[:-1])
                return timedelta(days=days)
            except ValueError:
                return False
        elif duration_lower.startswith("days:"):
            try:
                days = int(duration_lower[5:])
                return timedelta(days=days)
            except ValueError:
                return False
        else:
            return False
    
    def _set_premium(self, user_id_str, duration_str):
        """Set premium status untuk user"""
        # Validasi user_id
        user_id = self._validate_user_id(user_id_str)
        if user_id is None:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "user_id invalid."
            }
        
        # Validasi duration
        duration_delta = self._parse_duration(duration_str)
        if duration_delta is False:
            return {
                "status": "error", 
                "code": "DURATION_INVALID",
                "message": "Gunakan month|lifetime|<N>d|days:<N>."
            }
        
        # Check if user exists
        user_check = self.supabase.table('users').select('id').eq('telegram_id', user_id).execute()
        if not user_check.data:
            return {
                "status": "error",
                "code": "USER_NOT_FOUND", 
                "message": f"User {user_id} not found."
            }
        
        # Calculate premium_until
        if duration_delta is None:
            # Lifetime
            premium_until = None
            message = f"Premium set for user {user_id} as lifetime"
        else:
            premium_until = (datetime.now(timezone.utc) + duration_delta).isoformat()
            message = f"Premium set for user {user_id} until {premium_until}"
        
        # Update database
        update_data = {
            "is_premium": True,
            "premium_until": premium_until
        }
        
        result = self.supabase.table('users').update(update_data).eq('telegram_id', user_id).execute()
        
        if result.data:
            return {
                "status": "success",
                "message": message
            }
        else:
            return {
                "status": "error",
                "code": "DB_ERROR",
                "message": "Failed to update user premium status"
            }
    
    def _revoke_premium(self, user_id_str):
        """Revoke premium status"""
        user_id = self._validate_user_id(user_id_str)
        if user_id is None:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "user_id invalid."
            }
        
        # Check if user exists
        user_check = self.supabase.table('users').select('id').eq('telegram_id', user_id).execute()
        if not user_check.data:
            return {
                "status": "error",
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} not found."
            }
        
        # Update database
        update_data = {
            "is_premium": False,
            "premium_until": None
        }
        
        result = self.supabase.table('users').update(update_data).eq('telegram_id', user_id).execute()
        
        if result.data:
            return {
                "status": "success",
                "message": f"Premium revoked for user {user_id}"
            }
        else:
            return {
                "status": "error", 
                "code": "DB_ERROR",
                "message": "Failed to revoke premium"
            }
    
    def _grant_credits(self, user_id_str, amount_str):
        """Grant credits to user"""
        user_id = self._validate_user_id(user_id_str)
        if user_id is None:
            return {
                "status": "error",
                "code": "PARAM_INVALID", 
                "message": "user_id invalid."
            }
        
        try:
            amount = int(amount_str)
            if amount == 0:
                return {
                    "status": "error",
                    "code": "PARAM_INVALID",
                    "message": "amount cannot be zero."
                }
        except ValueError:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "amount must be integer."
            }
        
        # Check if user exists and get current credits
        user_check = self.supabase.table('users').select('id, credits').eq('telegram_id', user_id).execute()
        if not user_check.data:
            return {
                "status": "error", 
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} not found."
            }
        
        current_credits = user_check.data[0].get('credits', 0)
        new_credits = current_credits + amount
        
        # Update credits
        result = self.supabase.table('users').update({
            "credits": new_credits
        }).eq('telegram_id', user_id).execute()
        
        if result.data:
            return {
                "status": "success",
                "message": f"Added {amount} credits to user {user_id}",
                "data": {
                    "credits_added": amount,
                    "previous_credits": current_credits,
                    "new_total": new_credits
                }
            }
        else:
            return {
                "status": "error",
                "code": "DB_ERROR", 
                "message": "Failed to update credits"
            }
    
    def _check_user_status(self, user_id_str):
        """Check user status"""
        user_id = self._validate_user_id(user_id_str)
        if user_id is None:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "user_id invalid."
            }
        
        # Get user data
        result = self.supabase.table('users').select('*').eq('telegram_id', user_id).execute()
        if not result.data:
            return {
                "status": "error",
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} not found."
            }
        
        user_data = result.data[0]
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until')
        credits = user_data.get('credits', 0)
        
        # Determine premium type
        if is_premium:
            if premium_until is None:
                premium_type = "lifetime"
            else:
                premium_type = "timed"
        else:
            premium_type = "free"
        
        return {
            "status": "success", 
            "message": f"User status retrieved for {user_id}",
            "data": {
                "is_premium": is_premium,
                "premium_type": premium_type,
                "premium_until": premium_until,
                "credits": credits
            }
        }
