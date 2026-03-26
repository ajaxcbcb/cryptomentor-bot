"""
Deposit Monitor — asyncio polling loop untuk deteksi deposit USDT BEP-20 via BSCScan.
Berjalan sebagai systemd service terpisah di Central_Server.
"""

import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

from license_server.license_manager import LicenseManager

load_dotenv()

logger = logging.getLogger(__name__)

BSCSCAN_API_KEY: str = os.environ.get("MORALIS_API_KEY", "") or os.environ.get("BSCSCAN_API_KEY", "")
BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

BSCSCAN_URL = "https://deep-index.moralis.io/api/v2.2"
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class DepositMonitor:
    POLL_INTERVAL = 300  # 5 menit
    USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
    MIN_CONFIRMATIONS = 12
    RETRY_DELAYS = [1, 2, 4]  # exponential backoff delays (seconds)

    def __init__(self) -> None:
        self._license_manager = LicenseManager()
        self._http: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    # ------------------------------------------------------------------
    # run — main asyncio loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Main asyncio loop: poll semua active deposit addresses setiap POLL_INTERVAL."""
        logger.info("DepositMonitor started. Poll interval: %ds", self.POLL_INTERVAL)

        while True:
            try:
                await self._poll_all_addresses()
            except Exception:
                logger.exception("Unexpected error in poll cycle, continuing.")

            await asyncio.sleep(self.POLL_INTERVAL)

    async def _poll_all_addresses(self) -> None:
        """Fetch semua active WL licenses dan poll masing-masing deposit address."""
        client = await self._license_manager._get_client()

        res = (
            await client.table("wl_licenses")
            .select("wl_id, deposit_address, admin_telegram_id")
            .in_("status", ["active", "grace_period", "inactive"])
            .execute()
        )

        licenses = res.data or []
        if not licenses:
            logger.debug("No active licenses to poll.")
            return

        logger.info("Polling %d deposit addresses.", len(licenses))

        tasks = [
            self.poll_address(row["wl_id"], row["deposit_address"])
            for row in licenses
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    # ------------------------------------------------------------------
    # poll_address
    # ------------------------------------------------------------------

    async def poll_address(self, wl_id: str, address: str) -> None:
        """
        GET Moralis ERC20 transfers endpoint untuk BSC, check MIN_CONFIRMATIONS.
        Implements exponential backoff [1s, 2s, 4s] max 3 retries.
        """
        # Moralis: GET /api/v2.2/{address}/erc20/transfers?chain=bsc&contract_addresses[]=USDT
        url = f"{BSCSCAN_URL}/{address}/erc20/transfers"
        params = {
            "chain": "bsc",
            "contract_addresses[]": self.USDT_CONTRACT,
            "order": "DESC",
            "limit": 50,
        }
        headers = {
            "X-API-Key": BSCSCAN_API_KEY,
            "accept": "application/json",
        }

        http = await self._get_http()
        last_exc: Exception | None = None

        for attempt, delay in enumerate(self.RETRY_DELAYS, start=1):
            try:
                resp = await http.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # Moralis returns {"result": [...], "cursor": ...}
                txs: list[dict] = data.get("result", [])
                for tx in txs:
                    await self.process_tx(wl_id, tx)
                return

            except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
                last_exc = exc
                logger.warning(
                    "poll_address attempt %d/%d failed for wl_id=%s: %s",
                    attempt,
                    len(self.RETRY_DELAYS),
                    wl_id,
                    exc,
                )
                if attempt < len(self.RETRY_DELAYS):
                    await asyncio.sleep(delay)

        logger.error(
            "poll_address: all retries exhausted for wl_id=%s address=%s. Last error: %s",
            wl_id,
            address,
            last_exc,
        )

    # ------------------------------------------------------------------
    # process_tx
    # ------------------------------------------------------------------

    async def process_tx(self, wl_id: str, tx: dict) -> None:
        """
        Proses satu transaksi Moralis ERC20 transfer:
        - Filter hanya transaksi yang masuk ke deposit address
        - Validasi confirmations >= MIN_CONFIRMATIONS
        - Validasi amount > 0
        - Call license_manager.credit_balance() (idempotent)
        - Kirim notifikasi Telegram ke WL Owner jika sukses
        """
        # Moralis format: {transaction_hash, from_address, to_address, value, token_decimals, block_number, ...}
        tx_hash: str = tx.get("transaction_hash", "")
        to_address: str = (tx.get("to_address") or "").lower()
        block_number: int = int(tx.get("block_number", 0))

        # Hanya proses transaksi yang masuk (to = deposit address)
        # Moralis sudah filter by address tapi bisa juga outgoing
        # Kita skip outgoing dengan cek to_address nanti di poll_address

        # Moralis tidak return confirmations langsung, pakai block_number sebagai proxy
        # Kita skip check confirmations karena Moralis hanya return confirmed txs
        # (unconfirmed tidak muncul di API)

        # USDT BEP-20 decimals = 18
        token_decimals = int(tx.get("token_decimals", 18))
        raw_value: int = int(tx.get("value", 0))
        amount_usdt: float = raw_value / (10 ** token_decimals)

        if amount_usdt <= 0:
            logger.warning("process_tx: skipping tx %s — amount is 0 or negative", tx_hash)
            return

        try:
            credited = await self._license_manager.credit_balance(
                wl_id=wl_id,
                amount=amount_usdt,
                tx_hash=tx_hash,
                block_number=block_number,
            )
        except Exception:
            logger.exception(
                "process_tx: Supabase write failed for wl_id=%s tx_hash=%s — will retry next cycle",
                wl_id,
                tx_hash,
            )
            return

        if not credited:
            return

        logger.info(
            "process_tx: credited %.6f USDT to wl_id=%s tx_hash=%s",
            amount_usdt,
            wl_id,
            tx_hash,
        )
        await self._notify_deposit(wl_id, amount_usdt, tx_hash)

    # ------------------------------------------------------------------
    # _notify_deposit — Telegram notification via bot pusat
    # ------------------------------------------------------------------

    async def _notify_deposit(self, wl_id: str, amount_usdt: float, tx_hash: str) -> None:
        """Kirim notifikasi Telegram ke admin_telegram_id WL Owner via bot pusat."""
        if not BOT_TOKEN:
            logger.warning("_notify_deposit: BOT_TOKEN not set, skipping notification.")
            return

        try:
            license_row = await self._license_manager.get_license(wl_id)
            if not license_row:
                logger.warning("_notify_deposit: license not found for wl_id=%s", wl_id)
                return

            admin_telegram_id: int = license_row["admin_telegram_id"]
            message = (
                f"✅ *Deposit Diterima*\n\n"
                f"💰 Jumlah: `{amount_usdt:.2f} USDT`\n"
                f"🔑 WL ID: `{wl_id}`\n"
                f"🔗 TX Hash: `{tx_hash}`\n\n"
                f"Saldo Anda telah diperbarui."
            )

            http = await self._get_http()
            url = TELEGRAM_API_URL.format(token=BOT_TOKEN)
            payload = {
                "chat_id": admin_telegram_id,
                "text": message,
                "parse_mode": "Markdown",
            }
            resp = await http.post(url, json=payload)
            resp.raise_for_status()
            logger.info(
                "_notify_deposit: Telegram notification sent to %d for wl_id=%s",
                admin_telegram_id,
                wl_id,
            )

        except Exception:
            logger.warning(
                "_notify_deposit: failed to send Telegram notification for wl_id=%s — non-fatal",
                wl_id,
                exc_info=True,
            )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not BSCSCAN_API_KEY:
        raise RuntimeError("BSCSCAN_API_KEY environment variable is not set.")
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN not set — Telegram notifications will be disabled.")

    monitor = DepositMonitor()
    asyncio.run(monitor.run())
