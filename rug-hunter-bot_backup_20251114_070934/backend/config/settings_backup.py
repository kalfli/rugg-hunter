"""Configuration Settings - Complete"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Trading
    TRADING_MODE: str = "PAPER"
    
    # RPC Endpoints
    ETH_RPC_URL: str = "https://eth.llamarpc.com"
    BSC_RPC_URL: str = "https://bsc-dataseed1.binance.org"
    
    # API Keys
    ETHERSCAN_API_KEY: Optional[str] = None
    BSCSCAN_API_KEY: Optional[str] = None
    
    # Notifications
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    
    # Auto-Trading
    AUTO_TRADING_ENABLED: bool = False
    MIN_AUTO_TRADE_CONFIDENCE: int = 75
    MAX_AUTO_TRADES_PER_HOUR: int = 5
    
    # Wallet
    WALLET_KEYSTORE_PATH: str = "secure/keystore.json"
    
    # Risk Management
    MAX_PORTFOLIO_EXPOSURE_PERCENT: int = 20
    MAX_DAILY_LOSS_PERCENT: int = 15
    MAX_POSITION_SIZE_USD: int = 500
    
    # Detection
    ENABLE_ETH_DETECTION: bool = True
    ENABLE_BSC_DETECTION: bool = True
    MIN_LIQUIDITY_USD: int = 5000
    MAX_TOKEN_AGE_MINUTES: int = 30
    SCAN_BLOCK_INTERVAL: int = 3
    
    # Dashboard
    DASHBOARD_ENABLED: bool = True
    DASHBOARD_PORT: int = 3000
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        case_sensitive = True
