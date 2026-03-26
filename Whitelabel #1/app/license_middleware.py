"""
License Middleware — Block all user requests when license is suspended.
Checks license status before processing any update from users.
"""

import logging
from telegram import Update
from telegram.ext import BaseHandler, ContextTypes
from typing import Optional

logger = logging.getLogger(__name__)


class LicenseMiddleware(BaseHandler):
    """
    Middleware yang check license sebelum semua handler diproses.
    Jika license suspended, block semua user request dan kirim notifikasi.
    """

    def __init__(self, license_guard):
        super().__init__(self._callback)
        self.license_guard = license_guard
        self._last_check_time = 0
        self._check_interval = 60  # Check setiap 60 detik untuk mengurangi API calls
        self._cached_valid = True  # Assume valid initially

    async def _callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """This is never called — we override check_update instead."""
        pass

    def check_update(self, update: object) -> Optional[bool]:
        """
        Return True untuk semua update — kita akan handle di handle_update.
        Ini memastikan middleware dipanggil untuk semua update.
        """
        return True

    async def handle_update(
        self,
        update: Update,
        application,
        check_result,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """
        Check license sebelum update diproses.
        Jika license invalid, block update dan kirim pesan ke user.
        """
        # Skip check untuk update tanpa user (channel posts, etc)
        if not update.effective_user:
            return None

        # Skip check untuk admin (agar admin bisa tetap akses bot untuk troubleshooting)
        from config import ADMIN_IDS
        if update.effective_user.id in ADMIN_IDS:
            return None

        # Periodic check dengan cache untuk mengurangi API calls
        import time
        current_time = time.time()
        
        if current_time - self._last_check_time > self._check_interval:
            self._last_check_time = current_time
            self._cached_valid = await self.license_guard.check_license_valid()
            logger.debug(f"[LicenseMiddleware] License check: valid={self._cached_valid}")

        # Jika license tidak valid, block user dan kirim pesan
        if not self._cached_valid:
            logger.warning(
                f"[LicenseMiddleware] Blocking user {update.effective_user.id} — license suspended"
            )
            
            # Kirim pesan ke user bahwa bot suspended
            try:
                import os
                deposit_address = os.getenv("DEPOSIT_ADDRESS", "0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9")
                
                msg = (
                    "🚫 <b>Bot Temporarily Unavailable</b>\n\n"
                    "This bot is currently suspended due to license payment.\n\n"
                    "Please contact the bot administrator for more information."
                )
                
                if update.message:
                    await update.message.reply_text(msg, parse_mode='HTML')
                elif update.callback_query:
                    await update.callback_query.answer(
                        "⚠️ Bot suspended — contact admin",
                        show_alert=True
                    )
            except Exception as e:
                logger.error(f"[LicenseMiddleware] Failed to send suspended message: {e}")
            
            # Block update — return None agar tidak diproses handler lain
            return None

        # License valid — return None agar update dilanjutkan ke handler berikutnya
        return None
