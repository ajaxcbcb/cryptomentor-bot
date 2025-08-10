
#!/usr/bin/env python3
"""
AI Agent Server-side untuk Command Admin CryptoMentor AI
Mengelola status premium dan credits user dengan validasi keamanan
"""

import os
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from supabase import create_client, Client
import uuid

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
            supabase_key = <REDACTED_SUPABASE_KEY>
            
            if not supabase_url or not supabase_key:
                self.connection_status = {
                    "validated": False,
                    "error": {
                        "status": "error",
                        "code": "CONFIG_MISSING", 
                        "message": "Supabase belum dikonfigurasi dengan benar."
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
            
            # 5. Validasi struktur tabel
            schema_check = self.supabase.table('users').select('credits').limit(1).execute()
            
            self.connection_status = {"validated": True, "error": None}
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            if "relation \"public.users\" does not exist" in error_msg:
                error_code = "CONNECTION_FAILED"
                message = "Tabel 'users' tidak ditemukan di Supabase database."
            elif "column \"credits\" does not exist" in error_msg:
                error_code = "MISSING_COLUMN"
                message = "Kolom 'credits' tidak ditemukan di tabel users."
            elif "PGRST301" in error_msg or "authentication" in error_msg.lower():
                error_code = "CONNECTION_FAILED"
                message = "Authentication failed - check SUPABASE_SERVICE_ROLE_KEY."
            else:
                error_code = "CONNECTION_FAILED"
                message = "Gagal konek ke Supabase."
            
            self.connection_status = {
                "validated": False,
                "error": {
                    "status": "error",
                    "code": error_code,
                    "message": message
                }
            }
            return False
    
    def _validate_uuid(self, user_id: str) -> bool:
        """Validasi format UUID"""
        try:
            uuid.UUID(user_id)
            return True
        except ValueError:
            return False
    
    def _parse_duration(self, duration: str) -> Optional[datetime]:
        """Parse duration string ke datetime expiry"""
        try:
            duration = duration.lower().strip()
            current_time = datetime.now(timezone.utc)
            
            if duration in ['lifetime', 'seumur_hidup']:
                return None  # null = lifetime
            
            elif duration in ['month', 'months', 'bulan']:
                return current_time + timedelta(days=30)
            
            elif duration.endswith('d'):
                days = int(duration[:-1])
                return current_time + timedelta(days=days)
            
            elif duration.startswith('days:'):
                days = int(duration.split(':')[1])
                return current_time + timedelta(days=days)
            
            else:
                return None
                
        except (ValueError, IndexError):
            return None
    
    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Ambil data user berdasarkan ID"""
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    def execute_command(self, command: str, *args) -> Dict[str, Any]:
        """Execute admin command dengan validasi penuh"""
        
        # 1. Validasi koneksi Supabase
        if not self.connection_status["validated"]:
            return self.connection_status["error"]
        
        try:
            # 2. Route command ke handler yang sesuai
            if command == "/setpremium":
                return self._handle_setpremium(*args)
            elif command == "/revoke_premium":
                return self._handle_revoke_premium(*args)
            elif command == "/grant_credits":
                return self._handle_grant_credits(*args)
            else:
                return {
                    "status": "error",
                    "code": "PARAM_INVALID",
                    "message": f"Command '{command}' tidak dikenal."
                }
                
        except Exception as e:
            return {
                "status": "error",
                "code": "DB_ERROR",
                "message": f"Database error: {str(e)}"
            }
    
    def _handle_setpremium(self, user_id: str, duration: str) -> Dict[str, Any]:
        """Handle /setpremium command"""
        
        # 1. Validasi parameter
        if not user_id or not duration:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "Parameter tidak lengkap. Format: /setpremium <user_id> <duration>"
            }
        
        if not self._validate_uuid(user_id):
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "user_id harus UUID valid."
            }
        
        # 2. Parse duration
        premium_until = self._parse_duration(duration)
        if premium_until is False:  # Invalid format
            return {
                "status": "error",
                "code": "DURATION_INVALID",
                "message": "Gunakan month|lifetime|<N>d|days:<N>."
            }
        
        # 3. Cek user exists
        user = self._get_user_by_id(user_id)
        if not user:
            return {
                "status": "error",
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} tidak ditemukan."
            }
        
        # 4. Update premium status
        update_data = {
            "is_premium": True,
            "premium_until": premium_until.isoformat() if premium_until else None
        }
        
        result = self.supabase.table('users').update(update_data).eq('id', user_id).execute()
        
        if result.data:
            if premium_until is None:
                message = f"Premium set for user {user_id} as lifetime"
            else:
                message = f"Premium set for user {user_id} until {premium_until.isoformat()}"
            
            return {
                "status": "success",
                "message": message
            }
        else:
            return {
                "status": "error",
                "code": "DB_ERROR",
                "message": "Gagal update status premium."
            }
    
    def _handle_revoke_premium(self, user_id: str) -> Dict[str, Any]:
        """Handle /revoke_premium command"""
        
        # 1. Validasi parameter
        if not user_id:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "Parameter tidak lengkap. Format: /revoke_premium <user_id>"
            }
        
        if not self._validate_uuid(user_id):
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "user_id harus UUID valid."
            }
        
        # 2. Cek user exists
        user = self._get_user_by_id(user_id)
        if not user:
            return {
                "status": "error",
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} tidak ditemukan."
            }
        
        # 3. Revoke premium
        update_data = {
            "is_premium": False,
            "premium_until": None
        }
        
        result = self.supabase.table('users').update(update_data).eq('id', user_id).execute()
        
        if result.data:
            return {
                "status": "success",
                "message": f"Premium revoked for user {user_id}"
            }
        else:
            return {
                "status": "error",
                "code": "DB_ERROR",
                "message": "Gagal revoke premium."
            }
    
    def _handle_grant_credits(self, user_id: str, amount: str) -> Dict[str, Any]:
        """Handle /grant_credits command"""
        
        # 1. Validasi parameter
        if not user_id or not amount:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "Parameter tidak lengkap. Format: /grant_credits <user_id> <amount>"
            }
        
        if not self._validate_uuid(user_id):
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "user_id harus UUID valid."
            }
        
        try:
            credit_amount = int(amount)
            if credit_amount == 0:
                return {
                    "status": "error",
                    "code": "PARAM_INVALID",
                    "message": "amount harus integer non-zero."
                }
        except ValueError:
            return {
                "status": "error",
                "code": "PARAM_INVALID",
                "message": "amount harus integer valid."
            }
        
        # 2. Cek user exists dan ambil credits saat ini
        user = self._get_user_by_id(user_id)
        if not user:
            return {
                "status": "error",
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} tidak ditemukan."
            }
        
        current_credits = user.get('credits', 0) or 0
        new_credits = current_credits + credit_amount
        
        # 3. Update credits
        result = self.supabase.table('users').update({"credits": new_credits}).eq('id', user_id).execute()
        
        if result.data:
            return {
                "status": "success",
                "message": f"Added {credit_amount} credits to user {user_id}",
                "data": {
                    "new_credits": new_credits,
                    "previous_credits": current_credits
                }
            }
        else:
            return {
                "status": "error",
                "code": "DB_ERROR",
                "message": "Gagal update credits."
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status koneksi Supabase"""
        if self.connection_status["validated"]:
            return {
                "status": "success",
                "message": "Supabase sudah dikonfigurasi dengan benar. Siap untuk digunakan."
            }
        else:
            return self.connection_status["error"]


def main():
    """Test function untuk admin agent"""
    print("🤖 AI Agent Admin CryptoMentor AI")
    print("=" * 50)
    
    agent = AdminAgent()
    
    # Test koneksi
    status = agent.get_connection_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    if status["status"] == "success":
        print("\n✅ Agent siap menerima command admin!")
        print("Commands yang didukung:")
        print("- /setpremium <user_id> <month|lifetime|30d|days:N>")
        print("- /revoke_premium <user_id>")
        print("- /grant_credits <user_id> <amount>")


if __name__ == "__main__":
    main()
