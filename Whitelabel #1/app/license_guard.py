"""
License Guard — WL Bot startup & periodic license validation.
Checks license status via License API with local cache fallback.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


def _get_config():
    """Lazy import config to avoid circular imports."""
    from config import BOT_TOKEN, ADMIN_IDS
    return BOT_TOKEN, ADMIN_IDS


class LicenseGuard:
    CHECK_INTERVAL = 86400      # 24 jam
    CACHE_MAX_AGE  = 172800     # 48 jam
    API_TIMEOUT    = 10         # detik
    CACHE_FILE     = "data/license_cache.json"
    NOTIF_FLAG_FILE = "data/license_notif_sent.json"  # Track notifikasi yang sudah dikirim

    def __init__(self):
        self._wl_id          = os.getenv("WL_ID", "")
        self._secret_key     = os.getenv("WL_SECRET_KEY", "")
        self._api_url        = os.getenv("LICENSE_API_URL", "").rstrip("/")

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    async def startup_check(self) -> bool:
        """
        Dipanggil saat bot startup.
        Returns True jika bot boleh jalan, False jika harus halt.
        """
        # Development mode: skip license check jika LICENSE_API_URL kosong
        if not self._api_url or not self._wl_id or not self._secret_key:
            logger.info("[LicenseGuard] LICENSE_API_URL/WL_ID/SECRET_KEY not set — running in DEV MODE (no license check)")
            return True

        response = await self._call_api()

        if response is not None:
            # API berhasil dijangkau
            self._save_cache(response)

            if response.get("valid") is True:
                logger.info("[LicenseGuard] License valid — status: %s", response.get("status"))
                # Clear suspended notification flag jika license aktif kembali
                self._clear_notif_flag("suspended")
                await self._maybe_send_warning(response)
                return True

            if response.get("valid") is False and response.get("status") == "suspended":
                logger.error("[LicenseGuard] License suspended — halting bot")
                await self._notify_suspended()
                return False

            # valid: false tapi bukan suspended (misal: inactive)
            logger.warning("[LicenseGuard] License not valid — status: %s", response.get("status"))
            return False

        # API tidak bisa dijangkau — fallback ke cache
        logger.warning("[LicenseGuard] API unreachable, trying cache fallback")
        return await self._handle_cache_fallback()

    async def check_license_valid(self) -> bool:
        """
        Check apakah license valid saat ini (untuk middleware).
        Returns True jika valid, False jika suspended/invalid.
        Tidak mengirim notifikasi (sudah dikirim di startup_check).
        """
        # Development mode: skip license check
        if not self._api_url or not self._wl_id or not self._secret_key:
            return True

        response = await self._call_api()

        if response is not None:
            # API berhasil dijangkau
            self._save_cache(response)
            
            if response.get("valid") is True:
                # Clear suspended notification flag jika license aktif kembali
                self._clear_notif_flag("suspended")
                return True
            
            return False

        # API tidak bisa dijangkau — fallback ke cache
        cache = self._load_cache()
        if cache is None:
            return False

        cached_at = self._parse_cached_at(cache.get("cached_at"))
        if cached_at is None:
            return False

        age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
        
        if age_seconds < self.CACHE_MAX_AGE:
            return bool(cache.get("valid", False))
        
        return False

    async def periodic_check_loop(self):
        """Asyncio loop — check setiap CHECK_INTERVAL detik."""
        while True:
            await asyncio.sleep(self.CHECK_INTERVAL)
            logger.info("[LicenseGuard] Running periodic license check")
            try:
                result = await self.startup_check()
                if not result:
                    logger.error("[LicenseGuard] Periodic check failed — bot should halt")
                    # Raise untuk membiarkan caller menangani shutdown
                    raise RuntimeError("License check failed during periodic check")
            except RuntimeError:
                raise
            except Exception as exc:
                logger.error("[LicenseGuard] Periodic check error: %s", exc)

    # ──────────────────────────────────────────────────────────────
    # Cache
    # ──────────────────────────────────────────────────────────────

    def _load_cache(self) -> dict | None:
        """Baca cache file. Return None jika tidak ada atau corrupt."""
        try:
            path = Path(self.CACHE_FILE)
            if not path.exists():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            # Validasi minimal: harus ada cached_at
            if "cached_at" not in data:
                return None
            return data
        except (json.JSONDecodeError, OSError, KeyError):
            logger.warning("[LicenseGuard] Cache file corrupt or unreadable")
            return None

    def _save_cache(self, response: dict):
        """Tulis response + cached_at timestamp ke cache file."""
        try:
            Path(self.CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "valid":           response.get("valid"),
                "status":          response.get("status"),
                "expires_in_days": response.get("expires_in_days"),
                "balance":         response.get("balance"),
                "warning":         response.get("warning"),
                "cached_at":       datetime.now(timezone.utc).isoformat(),
            }
            Path(self.CACHE_FILE).write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
            logger.debug("[LicenseGuard] Cache saved")
        except OSError as exc:
            logger.error("[LicenseGuard] Failed to save cache: %s", exc)

    # ──────────────────────────────────────────────────────────────
    # API Call
    # ──────────────────────────────────────────────────────────────

    async def _call_api(self) -> dict | None:
        """
        POST ke LICENSE_API_URL/api/license/check.
        Return None jika network error atau timeout.
        """
        if not self._api_url or not self._wl_id or not self._secret_key:
            logger.error("[LicenseGuard] WL_ID, WL_SECRET_KEY, atau LICENSE_API_URL tidak dikonfigurasi")
            return None

        url = f"{self._api_url}/api/license/check"
        payload = {"wl_id": self._wl_id, "secret_key": self._secret_key}

        try:
            async with httpx.AsyncClient(timeout=self.API_TIMEOUT) as client:
                resp = await client.post(url, json=payload)

            if resp.status_code == 200:
                return resp.json()

            # 5xx → treat as network error (fallback ke cache)
            if resp.status_code >= 500:
                logger.warning("[LicenseGuard] API returned %s — treating as network error", resp.status_code)
                return None

            # 4xx (401, 404, 400) → kembalikan body agar startup_check bisa handle
            logger.warning("[LicenseGuard] API returned %s", resp.status_code)
            try:
                return resp.json()
            except Exception:
                return None

        except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as exc:
            logger.warning("[LicenseGuard] API unreachable: %s", exc)
            return None
        except Exception as exc:
            logger.error("[LicenseGuard] Unexpected API error: %s", exc)
            return None

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    async def _handle_cache_fallback(self) -> bool:
        """
        Gunakan cache jika cached_at < 48 jam.
        Halt (return False) jika cache > 48 jam atau tidak ada.
        """
        cache = self._load_cache()

        if cache is None:
            logger.error("[LicenseGuard] No cache available and API unreachable — halting bot")
            await self._notify_api_down_no_cache()
            return False

        cached_at = self._parse_cached_at(cache.get("cached_at"))
        if cached_at is None:
            logger.error("[LicenseGuard] Cache has invalid cached_at — halting bot")
            return False

        age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()

        if age_seconds < self.CACHE_MAX_AGE:
            logger.warning(
                "[LicenseGuard] Using cache (age: %.0f s / max: %s s)",
                age_seconds, self.CACHE_MAX_AGE
            )
            return bool(cache.get("valid", False))

        # Cache > 48 jam dan API down → halt
        logger.error(
            "[LicenseGuard] Cache too old (%.0f s) and API unreachable — halting bot",
            age_seconds
        )
        await self._notify_api_down_stale_cache()
        return False

    @staticmethod
    def _parse_cached_at(value: str | None) -> datetime | None:
        """Parse ISO 8601 string ke datetime dengan timezone."""
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None

    async def _maybe_send_warning(self, response: dict):
        """Kirim warning Telegram jika warning: true dan expires_in_days < 5."""
        if response.get("warning") and (response.get("expires_in_days", 99) < 5):
            days = response.get("expires_in_days", "?")
            balance = response.get("balance", 0)
            msg = (
                f"⚠️ *License Warning*\n"
                f"Lisensi bot akan berakhir dalam *{days} hari*.\n"
                f"Balance saat ini: *${balance:.2f} USDT*\n"
                f"Segera top-up untuk menghindari suspensi."
            )
            await self._send_telegram(msg)

    async def _notify_suspended(self):
        """Kirim notifikasi ke admin bahwa bot di-suspend (hanya 1x)."""
        # Cek apakah notifikasi suspended sudah pernah dikirim
        if self._check_notif_sent("suspended"):
            logger.info("[LicenseGuard] Suspended notification already sent, skipping")
            return
        
        # Get deposit address dari env atau database
        deposit_address = os.getenv("DEPOSIT_ADDRESS", "0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9")
        
        msg = (
            "🚫 *Bot Suspended - Payment Required*\n\n"
            "⚠️ Lisensi bot telah di-suspend karena balance habis.\n"
            "👥 User tidak bisa menggunakan bot sampai Anda membayar.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 *CARA PEMBAYARAN (OTOMATIS)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ Kirim USDT via *BSC Network* (Binance Smart Chain) ke:\n\n"
            f"📍 *Wallet Address:*\n"
            f"`{deposit_address}`\n\n"
            "2️⃣ Jumlah:\n"
            "   • Minimum: *$10 USDT* (1 bulan)\n"
            "   • Recommended: *$50 USDT* (5 bulan)\n"
            "   • Biaya bulanan: *$10/bulan*\n\n"
            "3️⃣ Setelah transfer:\n"
            "   ✅ Bot akan *otomatis aktif* dalam 5-10 menit\n"
            "   ✅ Tidak perlu konfirmasi manual\n"
            "   ✅ User langsung bisa pakai bot\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ *PENTING:*\n"
            "• Gunakan *BSC Network* (BEP20)\n"
            "• Jangan gunakan network lain (ETH/TRC20)\n"
            "• Deposit akan terdeteksi otomatis\n\n"
            "💡 Cek balance: /license_status"
        )
        await self._send_telegram(msg)
        
        # Mark notifikasi sudah dikirim
        self._mark_notif_sent("suspended")

    async def _notify_api_down_no_cache(self):
        """Kirim notifikasi: API down dan tidak ada cache."""
        msg = (
            "🔴 *License Check Failed*\n"
            "License API tidak dapat dijangkau dan tidak ada cache tersedia.\n"
            "Bot dihentikan untuk keamanan."
        )
        await self._send_telegram(msg)

    async def _notify_api_down_stale_cache(self):
        """Kirim notifikasi: API down dan cache sudah kadaluarsa."""
        msg = (
            "🔴 *License Check Failed*\n"
            "License API tidak dapat dijangkau dan cache sudah kadaluarsa (>48 jam).\n"
            "Bot dihentikan untuk keamanan."
        )
        await self._send_telegram(msg)

    async def _send_telegram(self, text: str):
        """Kirim pesan ke semua admin via Telegram Bot API."""
        try:
            bot_token, admin_ids = _get_config()
            if not bot_token or not admin_ids:
                logger.warning("[LicenseGuard] BOT_TOKEN atau ADMIN_IDS tidak dikonfigurasi, skip notifikasi")
                return

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            async with httpx.AsyncClient(timeout=10) as client:
                for admin_id in admin_ids:
                    try:
                        await client.post(url, json={
                            "chat_id":    admin_id,
                            "text":       text,
                            "parse_mode": "Markdown",
                        })
                    except Exception as exc:
                        logger.warning("[LicenseGuard] Failed to notify admin %s: %s", admin_id, exc)
        except Exception as exc:
            logger.error("[LicenseGuard] Telegram notification error: %s", exc)

    def _check_notif_sent(self, notif_type: str) -> bool:
        """Check apakah notifikasi tipe tertentu sudah pernah dikirim."""
        try:
            path = Path(self.NOTIF_FLAG_FILE)
            if not path.exists():
                return False
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get(notif_type, False)
        except (json.JSONDecodeError, OSError):
            return False

    def _mark_notif_sent(self, notif_type: str):
        """Mark notifikasi tipe tertentu sudah dikirim."""
        try:
            path = Path(self.NOTIF_FLAG_FILE)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing data
            data = {}
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
            
            # Update flag
            data[notif_type] = True
            data[f"{notif_type}_at"] = datetime.now(timezone.utc).isoformat()
            
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.debug("[LicenseGuard] Marked notification '%s' as sent", notif_type)
        except OSError as exc:
            logger.error("[LicenseGuard] Failed to mark notification: %s", exc)

    def _clear_notif_flag(self, notif_type: str):
        """Clear notifikasi flag (dipanggil saat license aktif kembali)."""
        try:
            path = Path(self.NOTIF_FLAG_FILE)
            if not path.exists():
                return
            
            data = json.loads(path.read_text(encoding="utf-8"))
            if notif_type in data:
                del data[notif_type]
                if f"{notif_type}_at" in data:
                    del data[f"{notif_type}_at"]
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                logger.debug("[LicenseGuard] Cleared notification flag '%s'", notif_type)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("[LicenseGuard] Failed to clear notification flag: %s", exc)

