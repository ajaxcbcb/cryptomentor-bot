"""
License Manager — CRUD layer ke Supabase pusat untuk Whitelabel License Billing.
Semua operasi write menggunakan service role key.
"""

import os
import uuid
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import AsyncClient, acreate_client

from license_server.wallet_manager import HDWalletManager

load_dotenv()

logger = logging.getLogger(__name__)


class LicenseManager:
    """
    CRUD layer ke Supabase pusat.
    Inisialisasi lazy — Supabase client dibuat saat pertama kali dibutuhkan.
    """

    def __init__(self) -> None:
        self._supabase_url: str = os.environ["SUPABASE_URL"]
        self._supabase_key: str = os.environ["SUPABASE_SERVICE_KEY"]
        mnemonic: str = os.environ["MASTER_SEED_MNEMONIC"]

        self._wallet = HDWalletManager(mnemonic)
        self._client: AsyncClient | None = None

    async def _get_client(self) -> AsyncClient:
        """Lazy-init async Supabase client."""
        if self._client is None:
            self._client = await acreate_client(self._supabase_url, self._supabase_key)
        return self._client

    # ------------------------------------------------------------------
    # register_wl
    # ------------------------------------------------------------------

    async def register_wl(self, admin_telegram_id: int, monthly_fee: float) -> dict:
        """
        Register a new Whitelabel license.

        Steps:
        1. Fetch all existing deposit_index values from wl_licenses.
        2. Compute next available index via HDWalletManager.get_next_index.
        3. Derive deposit_address for that index.
        4. Generate secret_key as UUID v4.
        5. INSERT row into wl_licenses.

        Returns:
            {"wl_id": str, "secret_key": str, "deposit_address": str}
        """
        client = await self._get_client()

        # Fetch used indices
        res = await client.table("wl_licenses").select("deposit_index").execute()
        used_indices: list[int] = [row["deposit_index"] for row in (res.data or [])]

        deposit_index = self._wallet.get_next_index(used_indices)
        deposit_address = self._wallet.derive_address(deposit_index)
        secret_key = str(uuid.uuid4())

        row = {
            "admin_telegram_id": admin_telegram_id,
            "monthly_fee": monthly_fee,
            "deposit_index": deposit_index,
            "deposit_address": deposit_address,
            "secret_key": secret_key,
            # expires_at defaults to NOW() + 0 days (inactive until first billing)
            "expires_at": datetime.now(timezone.utc).isoformat(),
            "status": "inactive",
        }

        insert_res = await client.table("wl_licenses").insert(row).execute()
        inserted = insert_res.data[0]

        return {
            "wl_id": inserted["wl_id"],
            "secret_key": inserted["secret_key"],
            "deposit_address": inserted["deposit_address"],
        }

    # ------------------------------------------------------------------
    # get_license
    # ------------------------------------------------------------------

    async def get_license(self, wl_id: str) -> dict | None:
        """
        Fetch a single license row by wl_id.

        Returns:
            dict with all wl_licenses columns, or None if not found.
        """
        client = await self._get_client()

        res = (
            await client.table("wl_licenses")
            .select("*")
            .eq("wl_id", wl_id)
            .maybe_single()
            .execute()
        )
        return res.data  # None if not found

    # ------------------------------------------------------------------
    # credit_balance
    # ------------------------------------------------------------------

    async def credit_balance(
        self,
        wl_id: str,
        amount: float,
        tx_hash: str,
        block_number: int,
    ) -> bool:
        """
        Atomically credit a deposit to a WL license.

        Idempotent: returns False immediately if tx_hash already exists in
        wl_deposits (UNIQUE constraint), without modifying balance.

        Steps:
        1. Check if tx_hash already processed.
        2. INSERT into wl_deposits.
        3. UPDATE wl_licenses.balance_usdt += amount.

        Returns:
            True  — deposit credited successfully.
            False — tx_hash already processed (idempotent no-op).
        """
        client = await self._get_client()

        # Idempotency check — avoid relying solely on DB exception for clarity
        existing = (
            await client.table("wl_deposits")
            .select("id")
            .eq("tx_hash", tx_hash)
            .maybe_single()
            .execute()
        )
        if existing.data is not None:
            logger.debug("credit_balance: tx_hash %s already processed, skipping.", tx_hash)
            return False

        # INSERT deposit record
        deposit_row = {
            "wl_id": wl_id,
            "tx_hash": tx_hash,
            "amount_usdt": amount,
            "block_number": block_number,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        }
        await client.table("wl_deposits").insert(deposit_row).execute()

        # UPDATE balance — use RPC for atomic increment to avoid race conditions
        await client.rpc(
            "increment_balance",
            {"p_wl_id": wl_id, "p_amount": amount},
        ).execute()

        logger.info(
            "credit_balance: credited %.6f USDT to wl_id=%s tx_hash=%s",
            amount,
            wl_id,
            tx_hash,
        )
        return True

    # ------------------------------------------------------------------
    # debit_billing
    # ------------------------------------------------------------------

    async def debit_billing(self, wl_id: str) -> dict:
        """
        Trigger atomic billing for a WL license via Supabase RPC process_billing.

        Returns:
            {
                "success": bool,
                "balance_before": float,
                "balance_after": float,
                "new_status": str,
                "expires_at": str,  # ISO 8601
            }
        """
        client = await self._get_client()

        res = await client.rpc("process_billing", {"p_wl_id": wl_id}).execute()

        # Supabase RPC returns the JSON result directly in res.data
        result: dict = res.data
        logger.info(
            "debit_billing: wl_id=%s success=%s new_status=%s",
            wl_id,
            result.get("success"),
            result.get("new_status"),
        )
        return result
