"""Wallet Setup Script"""
import getpass
import json
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from eth_account import Account

def main():
    print("=" * 60)
    print("RUG HUNTER WALLET SETUP")
    print("=" * 60)

    password = getpass.getpass("Master password (min 12 chars): ")
    if len(password) < 12:
        print("❌ Password too short")
        return

    key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
    fernet = Fernet(key)

    account = Account.create()
    print(f"✅ New wallet: {account.address}")
    print(f"⚠️ Save private key: {account.key.hex()}")

    keystore = {
        "wallets": [{
            "address": account.address,
            "private_key_encrypted": fernet.encrypt(account.key.hex().encode()).decode(),
            "chain": "ETH",
            "label": "Main Trading Wallet"
        }]
    }

    Path("secure").mkdir(exist_ok=True)
    with open("secure/keystore.json", "w") as f:
        json.dump(keystore, f, indent=2)

    print("✅ Keystore saved")
    print(f"📝 Send ETH to: {account.address}")

if __name__ == "__main__":
    main()
