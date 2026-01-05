#!/bin/bash

# 🚀 RUG HUNTER BOT V3.0 - Script de Correction d'Installation
# Ce script corrige les erreurs de configuration et met à jour les fichiers

set -e

echo "=============================================================================="
echo "🔧 RUG HUNTER BOT V3.0 - Correction d'Installation"
echo "=============================================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Vérifier qu'on est dans le bon répertoire
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Erreur: Exécutez ce script depuis la racine du projet${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Répertoire correct"
echo ""

# 2. Backup des fichiers existants
echo "📦 Sauvegarde des fichiers existants..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups/$timestamp

if [ -f "backend/config/settings.py" ]; then
    cp backend/config/settings.py backups/$timestamp/settings.py.bak
    echo -e "${GREEN}✓${NC} settings.py sauvegardé"
fi

if [ -f ".env" ]; then
    cp .env backups/$timestamp/.env.bak
    echo -e "${GREEN}✓${NC} .env sauvegardé"
fi

echo ""

# 3. Créer le nouveau settings.py
echo "📝 Création du nouveau settings.py..."
cat > backend/config/settings.py << 'EOF'
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
EOF

echo -e "${GREEN}✓${NC} settings.py créé"
echo ""

# 4. Créer/Mettre à jour .env si nécessaire
if [ ! -f ".env" ]; then
    echo "📝 Création du fichier .env..."
    cat > .env << 'EOF'
# RUG HUNTER BOT V3.0 - Configuration
TRADING_MODE=PAPER
ETH_RPC_URL=https://eth.llamarpc.com
BSC_RPC_URL=https://bsc-dataseed1.binance.org
SOL_RPC_URL=https://api.mainnet-beta.solana.com

ENABLE_ETH_DETECTION=True
ENABLE_BSC_DETECTION=True
ENABLE_SOL_DETECTION=True
MIN_LIQUIDITY_USD=5000
MAX_TOKEN_AGE_MINUTES=30
SCAN_BLOCK_INTERVAL=3

AUTO_TRADING_ENABLED=False
MIN_AUTO_TRADE_CONFIDENCE=75
MAX_POSITION_SIZE_USD=500
MAX_DAILY_LOSS_PERCENT=15

MAX_BUY_TAX=10
MAX_SELL_TAX=15
BLOCK_UNVERIFIED=True

ENABLE_HONEYPOT_DETECTION=True
ENABLE_TRAILING_STOPS=True
EOF
    echo -e "${GREEN}✓${NC} .env créé"
else
    echo -e "${YELLOW}⚠${NC}  .env existe déjà - pas de modification"
    echo "   Vérifiez manuellement que tous les paramètres sont présents"
fi

echo ""

# 5. Vérifier les dépendances Python
echo "🔍 Vérification des dépendances Python..."
if command -v python3 &> /dev/null; then
    python3 -c "import fastapi, uvicorn, websockets, aiohttp, web3" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Dépendances principales installées"
    else
        echo -e "${YELLOW}⚠${NC}  Certaines dépendances manquent"
        echo "   Exécutez: pip install -r backend/requirements.txt"
    fi
else
    echo -e "${RED}❌${NC} Python3 non trouvé"
fi

echo ""

# 6. Résumé
echo "=============================================================================="
echo "✅ Correction terminée !"
echo "=============================================================================="
echo ""
echo "Fichiers sauvegardés dans: backups/$timestamp/"
echo ""
echo "Prochaines étapes:"
echo "1. Vérifiez le fichier .env et ajoutez vos clés API si besoin"
echo "2. Lancez le bot avec: python3 startup_script.py"
echo "   ou directement: cd backend && python3 main_improved.py"
echo ""
echo "Documentation:"
echo "  - Guide d'installation: voir les artifacts créés"
echo "  - Configuration: éditez le fichier .env"
echo "  - Dashboard: http://localhost:8000 une fois le bot lancé"
echo ""
echo "⚠️  IMPORTANT: Testez toujours en mode PAPER avant LIVE !"
echo ""
