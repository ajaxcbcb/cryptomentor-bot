"""
HD Wallet Manager for Whitelabel License Billing.
Stateless utility — no network I/O, pure cryptographic derivation.
"""

from bip_utils import (
    Bip39MnemonicValidator,
    Bip39SeedGenerator,
    Bip44,
    Bip44Coins,
    Bip44Changes,
)
from eth_account import Account


class HDWalletManager:
    """
    Derives BSC/ETH deposit addresses from a BIP-39 mnemonic using BIP-44 path.
    Path: m/44'/60'/0'/0/{index}  (MetaMask-compatible ETH/BSC path)
    """

    def __init__(self, mnemonic: str) -> None:
        """
        Initialize with a BIP-39 mnemonic.

        Raises:
            RuntimeError: if mnemonic is empty or blank.
            ValueError: if mnemonic is not a valid BIP-39 mnemonic.
        """
        if not mnemonic or not mnemonic.strip():
            raise RuntimeError("MASTER_SEED_MNEMONIC is required but was empty.")

        if not Bip39MnemonicValidator().IsValid(mnemonic):
            raise ValueError(f"Invalid BIP-39 mnemonic provided.")

        self._seed = Bip39SeedGenerator(mnemonic).Generate()

    def derive_address(self, index: int) -> str:
        """
        Derive a checksummed BSC/ETH address at BIP-44 path m/44'/60'/0'/0/{index}.

        Args:
            index: Non-negative integer address index.

        Returns:
            EIP-55 checksummed Ethereum/BSC address string.
        """
        bip44_ctx = (
            Bip44.FromSeed(self._seed, Bip44Coins.ETHEREUM)
            .Purpose()
            .Coin()
            .Account(0)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(index)
        )
        private_key_bytes = bip44_ctx.PrivateKey().Raw().ToBytes()
        account = Account.from_key(private_key_bytes)
        return account.address  # eth_account returns EIP-55 checksummed address

    def get_next_index(self, used_indices: list[int]) -> int:
        """
        Return the smallest non-negative integer not in used_indices.

        Args:
            used_indices: List of already-used deposit indices.

        Returns:
            Minimum unused index >= 0.
        """
        used_set = set(used_indices)
        index = 0
        while index in used_set:
            index += 1
        return index
