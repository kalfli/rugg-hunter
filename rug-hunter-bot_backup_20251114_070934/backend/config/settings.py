"""Configuration Settings - Complete V3.0"""
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
    SOL_RPC_URL: str = "https://api.mainnet-beta.solana.com"
    
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
    WALLET_PRIVATE_KEY: Optional[str] = None
    
    # Risk Management
    MAX_PORTFOLIO_EXPOSURE_PERCENT: int = 20
    MAX_DAILY_LOSS_PERCENT: int = 15
    MAX_POSITION_SIZE_USD: int = 500
    MAX_CONCURRENT_POSITIONS: int = 5
    MAX_LOSS_PER_TRADE_PERCENT: float = 5.0
    MAX_WEEKLY_LOSS_PERCENT: int = 30
    COOLDOWN_AFTER_LOSS_MINUTES: int = 30
    
    # Detection
    ENABLE_ETH_DETECTION: bool = True
    ENABLE_BSC_DETECTION: bool = True
    ENABLE_SOL_DETECTION: bool = True
    MIN_LIQUIDITY_USD: int = 5000
    MAX_TOKEN_AGE_MINUTES: int = 30
    SCAN_BLOCK_INTERVAL: int = 3
    MIN_HOLDERS: int = 50
    MAX_TOP_HOLDER_PERCENT: float = 20.0
    MAX_TOP10_HOLDERS_PERCENT: float = 50.0
    MIN_VOLUME_24H_USD: float = 1000.0
    MAX_PRICE_VOLATILITY_1H: float = 50.0
    
    # Dashboard
    DASHBOARD_ENABLED: bool = True
    DASHBOARD_PORT: int = 3000
    
    # V3.0 Features
    ENABLE_HONEYPOT_DETECTION: bool = True
    ENABLE_MEMPOOL_MONITORING: bool = False
    ENABLE_TRAILING_STOPS: bool = True
    ENABLE_MULTI_RPC_FAILOVER: bool = True
    
    # Honeypot Protection
    MAX_BUY_TAX: int = 10
    MAX_SELL_TAX: int = 15
    BLOCK_UNVERIFIED: bool = True
    REQUIRE_OWNERSHIP_RENOUNCED: bool = False
    
    # Trading Parameters
    DEFAULT_STOP_LOSS_PERCENT: float = 5.0
    DEFAULT_TAKE_PROFIT_PERCENT: float = 20.0
    USE_TRAILING_STOP: bool = True
    TRAILING_STOP_ACTIVATION_PERCENT: float = 10.0
    TRAILING_STOP_DISTANCE_PERCENT: float = 5.0
    
    # Solana Specific
    SOL_REQUIRE_NO_FREEZE_AUTHORITY: bool = True
    SOL_REQUIRE_NO_MINT_AUTHORITY: bool = True
    SOL_MIN_ACCOUNT_AGE_SECONDS: int = 300
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'allow'

settings = Settings()
