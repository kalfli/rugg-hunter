"""Wallet Manager with Encryption"""
from cryptography.fernet import Fernet
from eth_account import Account
import json
import hashlib
import base64
from pathlib import Path

class WalletManager:
    def __init__(self, keystore_path: str, master_password: str):
        self.keystore_path = Path(keystore_path)
        self.encryption_key = self._derive_key(master_password)
        self.fernet = Fernet(self.encryption_key)
        self.wallets = self._load_and_decrypt()
        self.active_index = 0

    def _derive_key(self, password: str) -> bytes:
        hash_digest = hashlib.sha256(password.encode()).digest()
        return base64.urlsafe_b64encode(hash_digest)

    def _load_and_decrypt(self):
        if not self.keystore_path.exists():
            raise FileNotFoundError(f"Keystore not found: {self.keystore_path}")
        with open(self.keystore_path, 'r') as f:
            return json.load(f).get("wallets", [])

    def get_active_wallet(self):
        wallet_data = self.wallets[self.active_index]
        private_key = self.fernet.decrypt(wallet_data["private_key_encrypted"].encode()).decode()
        return Account.from_key(private_key)

    def is_connected(self):
        return len(self.wallets) > 0
