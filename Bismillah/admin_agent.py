#!/usr/bin/env python3
"""
AI Agent Server-side untuk Command Admin CryptoMentor AI
Mengelola status premium dan credits user dengan validasi keamanan
"""

import os
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

class AdminAgent:
    """AI Agent untuk menjalankan command admin secara aman"""

    def __init__(self):
        self.supabase = None
        self.connection_status = {"validated": False, "error": None}
        self._validate_and_init_supabase()

    def _validate_and_init_supabase(self) -> bool:
        """Validasi konfigurasi dan inisialisasi koneksi Supabase"""
        # TODO: Implement database connection after setup
        self.connection_status = {
            "validated": False,
            "error": {
                "status": "error",
                "code": "CONFIG_MISSING",
                "message": "Database integration not configured."
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
        # TODO: Implement user data retrieval
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
        # TODO: Implement premium status update
        update_success = False # Placeholder

        if update_success:
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
        # TODO: Implement premium status update
        update_success = False # Placeholder

        if update_success:
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
        # TODO: Implement credits update
        update_success = False # Placeholder

        if update_success:
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
                "message": "Database connection is ready."
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