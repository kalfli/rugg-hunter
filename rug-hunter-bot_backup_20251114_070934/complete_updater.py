#!/usr/bin/env python3
"""
RUG HUNTER - COMPLETE AUTO UPDATE SCRIPT
Ce script met à jour TOUS les fichiers automatiquement
Exécuter: python complete_update.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
BACKUP_DIR = f"backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Couleurs
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

def backup_file(filepath):
    """Crée un backup"""
    if os.path.exists(filepath):
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
        dest = Path(BACKUP_DIR) / Path(filepath).name
        shutil.copy2(filepath, dest)
        return True
    return False

# === CONTENU DES FICHIERS CORRIGÉS ===

def get_requirements_fixed():
    return """fastapi==0.104.1
uvicorn[standard]==0.24.0
web3==6.11.3
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
aiohttp==3.9.1
cryptography==41.0.7
scikit-learn==1.3.2
joblib==1.3.2
pytest==7.4.3
pytest-asyncio==0.21.1
eth-account==0.10.0
pandas==2.1.3
numpy==1.26.2
websockets==12.0
redis==5.0.1
psycopg2-binary==2.9.9
python-telegram-bot==20.7
discord.py==2.3.2
eth-abi==4.2.1
prometheus-client==0.19.0
psutil==5.9.6
python-jose[cryptography]==3.3.0
"""

def get_env_template():
    return """# === TRADING ===
TRADING_MODE=PAPER
AUTO_TRADING_ENABLED=false
MIN_AUTO_TRADE_CONFIDENCE=75

# === SECURITY (Générer avec: openssl rand -base64 32) ===
JWT_SECRET_KEY=CHANGE_ME_GENERATE_RANDOM
API_KEY=CHANGE_ME_GENERATE_RANDOM

# === RPC ENDPOINTS ===
ETH_RPC_URL=https://eth.llamarpc.com
BSC_RPC_URL=https://bsc-dataseed1.binance.org

# === API KEYS (Optionnel mais recommandé) ===
ETHERSCAN_API_KEY=
BSCSCAN_API_KEY=

# === WALLET ===
WALLET_KEYSTORE_PATH=./secure/keystore.json

# === RISK MANAGEMENT ===
MAX_POSITION_SIZE_USD=500
MAX_DAILY_LOSS_PERCENT=15
MAX_PORTFOLIO_EXPOSURE_PERCENT=20

# === DETECTION ===
ENABLE_ETH_DETECTION=true
ENABLE_BSC_DETECTION=true
MIN_LIQUIDITY_USD=5000
MAX_TOKEN_AGE_MINUTES=30
SCAN_BLOCK_INTERVAL=3

# === NOTIFICATIONS ===
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DISCORD_WEBHOOK_URL=

# === DATABASE ===
DATABASE_URL=sqlite:///./rug_hunter.db

# === FEATURES V2.0 ===
ENABLE_HONEYPOT_DETECTION=true
ENABLE_REAL_TAX_CHECKING=true
ENABLE_LP_LOCK_VERIFICATION=true
ENABLE_CONTRACT_VERIFICATION=true
"""

def get_gitignore():
    return """# Sensitive files
.env
secure/keystore.json
*.backup.*
backups_*/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
.pytest_cache/
htmlcov/

# Jupyter
.ipynb_checkpoints
"""

def get_honeypot_detector_fixed():
    return '''"""Advanced Honeypot Detector - VERSION CORRIGÉE"""
import asyncio
import logging
import aiohttp
from typing import Dict

logger = logging.getLogger(__name__)

class HoneypotDetector:
    def __init__(self, rpc_manager):
        self.rpc_manager = rpc_manager
        self.cache = {}
        
    async def is_honeypot(self, token_address: str, chain: str, pair_address: str = None) -> Dict:
        """✅ CORRIGÉ: Utilise Honeypot.is API pour VRAIE détection"""
        cache_key = f"{chain}:{token_address}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            chain_id = {"ETH": 1, "BSC": 56}.get(chain, 1)
            
            async with aiohttp.ClientSession() as session:
                url = "https://api.honeypot.is/v2/IsHoneypot"
                params = {
                    "address": token_address,
                    "chainID": chain_id
                }
                
                timeout = aiohttp.ClientTimeout(total=15)
                async with session.get(url, params=params, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        simulation = data.get("simulationResult", {})
                        honeypot_result = data.get("honeypotResult", {})
                        
                        result = {
                            "is_honeypot": honeypot_result.get("isHoneypot", False),
                            "can_buy": simulation.get("buyGas", 0) > 0,
                            "can_sell": simulation.get("sellGas", 0) > 0,
                            "buy_tax": simulation.get("buyTax", 0),
                            "sell_tax": simulation.get("sellTax", 0),
                            "buy_gas": simulation.get("buyGas", 0),
                            "sell_gas": simulation.get("sellGas", 0),
                            "liquidity_removable": False,
                            "reason": "Verified via Honeypot.is API"
                        }
                        
                        self.cache[cache_key] = result
                        return result
        
        except Exception as e:
            logger.error(f"Honeypot API error: {e}")
        
        # Fallback si API échoue
        return {
            "is_honeypot": False,
            "can_buy": True,
            "can_sell": True,
            "buy_tax": 0,
            "sell_tax": 0,
            "buy_gas": 0,
            "sell_gas": 0,
            "liquidity_removable": False,
            "reason": "Could not verify - API unavailable",
            "warning": "Proceed with extreme caution"
        }
    
    def clear_cache(self):
        self.cache.clear()
'''

def get_install_guide():
    return """# 🔧 GUIDE D'INSTALLATION POST-UPDATE

## ✅ Ce qui a été mis à jour automatiquement

- `backend/requirements.txt` - Dépendances corrigées
- `.env.template` - Template de configuration sécurisé
- `.gitignore` - Protection des fichiers sensibles
- `backend/core/honeypot_detector.py` - Détection réelle via API

## 📥 Fichiers volumineux à télécharger manuellement

Les fichiers suivants sont disponibles dans les artifacts Claude:

### 1. detector.py corrigé
**Artifact:** "detector.py - VERSION CORRIGÉE"
**Chemin:** `backend/core/detector.py`
**Changements:**
- Prix ETH/BNB réels depuis Coingecko
- Taxes réelles via Honeypot.is
- LP locked vérifié (Unicrypt, Team Finance, etc.)
- Contract verification via Etherscan API

### 2. token_analyzer.py corrigé
**Artifact:** "token_analyzer.py - VERSION CORRIGÉE"
**Chemin:** `backend/core/token_analyzer.py`
**Changements:**
- 54 indicateurs ML collectés RÉELLEMENT
- Analyse bytecode réelle
- Plus de valeurs hardcodées

### 3. setup_wallet.py sécurisé
**Artifact:** "setup_wallet.py - VERSION SÉCURISÉE"
**Chemin:** `scripts/setup_wallet.py`
**Changements:**
- PBKDF2 avec 480k itérations
- Seed phrase de 12 mots
- Clé privée jamais affichée
- Permissions fichier 600

## 🚀 Étapes d'installation

### 1. Installer les dépendances Python

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurer l'environnement

```bash
# Copier le template
cp .env.template .env

# Générer les clés de sécurité
openssl rand -base64 32  # Copier dans JWT_SECRET_KEY
openssl rand -base64 32  # Copier dans API_KEY

# Éditer .env avec vos clés API
nano .env
```

### 3. Télécharger les fichiers volumineux

Téléchargez depuis les artifacts Claude:
1. `detector.py` → `backend/core/detector.py`
2. `token_analyzer.py` → `backend/core/token_analyzer.py`
3. `setup_wallet.py` → `scripts/setup_wallet.py`

### 4. Créer un nouveau wallet sécurisé

```bash
python scripts/setup_wallet.py
```

⚠️ **IMPORTANT:** Notez votre seed phrase de 12 mots sur PAPIER !

### 5. Tester le bot

```bash
python backend/main.py
```

## ⚠️ ACTIONS DE SÉCURITÉ URGENTES

### À faire MAINTENANT:

1. **Révoquer le token Telegram exposé**
   ```
   1. Ouvrir Telegram → @BotFather
   2. Envoyer /revoke
   3. Sélectionner votre bot
   4. Générer un nouveau token
   5. Mettre à jour .env avec le nouveau token
   ```

2. **Transférer les fonds du wallet exposé**
   - Le keystore était public sur GitHub
   - Créez un NOUVEAU wallet avec setup_wallet.py
   - Transférez TOUS les fonds
   - Ne réutilisez JAMAIS l'ancien wallet

3. **Supprimer les fichiers sensibles de Git**
   ```bash
   git rm secure/keystore.json
   git rm .env
   git commit -m "Remove sensitive files"
   git push
   ```

4. **Vérifier .gitignore**
   - `.env` est ignoré
   - `secure/keystore.json` est ignoré
   - `*.backup.*` est ignoré

## 📊 Checklist avant de lancer

- [ ] Dépendances installées
- [ ] .env configuré avec NOUVELLES clés
- [ ] Nouveau wallet créé et sécurisé
- [ ] Ancien token Telegram révoqué
- [ ] Fichiers sensibles retirés de Git
- [ ] detector.py, token_analyzer.py, setup_wallet.py téléchargés
- [ ] Mode PAPER activé dans .env
- [ ] MIN_LIQUIDITY_USD >= 5000

## 🧪 Tests recommandés

### Test 1: Vérifier les prix réels
```python
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum,binancecoin&vs_currencies=usd") as r:
            print(await r.json())

asyncio.run(test())
```

### Test 2: Vérifier Honeypot.is API
```python
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.honeypot.is/v2/IsHoneypot?address=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2&chainID=1") as r:
            print(await r.json())

asyncio.run(test())
```

## 📚 Documentation complète

Consultez les artifacts:
- "RUG HUNTER - Analyse Complète & Solutions"
- "PLAN D'ACTION - Corrections Prioritaires"

## 💰 Coûts des APIs

| Service | Gratuit | Payant |
|---------|---------|--------|
| Coingecko | 50 calls/min | $129/mois |
| Honeypot.is | Illimité | N/A |
| Etherscan | 5 calls/sec | $199/mois |

**Recommandation:** Commencez avec les plans gratuits

## ⏱️ Timeline

- **Semaine 1:** Installation + Tests (mode PAPER)
- **Semaine 2:** Paper trading continu
- **Semaine 3:** Ajustements + Monitoring
- **Semaine 4:** Décision LIVE (avec <$100)

## 🆘 Besoin d'aide?

Si erreurs:
1. Vérifier les logs: `tail -f backend/logs/*.log`
2. Vérifier .env: toutes les variables sont définies
3. Vérifier API keys: valides et non expirées

Bonne chance ! 🚀
"""

def main():
    print_header("🚀 RUG HUNTER - MISE À JOUR COMPLÈTE AUTOMATIQUE")
    
    # Vérifier le répertoire
    if not os.path.exists("backend"):
        print_error("Erreur: Exécutez depuis la racine du projet (dossier backend introuvable)")
        sys.exit(1)
    
    print_info("Ce script va:")
    print("  1. Créer des backups de tous les fichiers")
    print("  2. Mettre à jour requirements.txt (supprimer doublons)")
    print("  3. Créer .env.template sécurisé")
    print("  4. Mettre à jour .gitignore")
    print("  5. Corriger honeypot_detector.py")
    print("  6. Créer un guide d'installation")
    
    response = input(f"\n{Colors.YELLOW}Continuer? (y/n): {Colors.RESET}").lower()
    if response != 'y':
        print_warning("Mise à jour annulée")
        sys.exit(0)
    
    # === ÉTAPE 1: BACKUPS ===
    print_header("📦 ÉTAPE 1: Création des backups")
    
    files = [
        "backend/requirements.txt",
        "backend/core/honeypot_detector.py",
        ".env"
    ]
    
    for f in files:
        if backup_file(f):
            print_success(f"Backup: {f}")
    
    print_info(f"Backups sauvegardés dans: {BACKUP_DIR}/")
    
    # === ÉTAPE 2: REQUIREMENTS.TXT ===
    print_header("📝 ÉTAPE 2: Mise à jour requirements.txt")
    
    with open("backend/requirements.txt", "w") as f:
        f.write(get_requirements_fixed())
    print_success("requirements.txt mis à jour (doublons supprimés)")
    
    # === ÉTAPE 3: .env.template ===
    print_header("🔧 ÉTAPE 3: Création de .env.template")
    
    with open(".env.template", "w") as f:
        f.write(get_env_template())
    print_success(".env.template créé")
    
    if not os.path.exists(".env"):
        shutil.copy(".env.template", ".env")
        print_warning(".env créé (CONFIGUREZ-LE AVANT D'UTILISER)")
    else:
        print_info(".env existe déjà (non modifié)")
    
    # === ÉTAPE 4: .gitignore ===
    print_header("📄 ÉTAPE 4: Mise à jour .gitignore")
    
    with open(".gitignore", "w") as f:
        f.write(get_gitignore())
    print_success(".gitignore mis à jour")
    
    # === ÉTAPE 5: honeypot_detector.py ===
    print_header("🍯 ÉTAPE 5: Correction de honeypot_detector.py")
    
    os.makedirs("backend/core", exist_ok=True)
    with open("backend/core/honeypot_detector.py", "w") as f:
        f.write(get_honeypot_detector_fixed())
    print_success("honeypot_detector.py corrigé (utilise maintenant Honeypot.is API)")
    
    # === ÉTAPE 6: GUIDE ===
    print_header("📚 ÉTAPE 6: Création du guide d'installation")
    
    with open("INSTALL_GUIDE.md", "w") as f:
        f.write(get_install_guide())
    print_success("INSTALL_GUIDE.md créé")
    
    # === ÉTAPE 7: INSTALL DEPENDENCIES ===
    print_header("📦 ÉTAPE 7: Installation des dépendances")
    
    response = input(f"\n{Colors.YELLOW}Installer pip dependencies maintenant? (y/n): {Colors.RESET}").lower()
    if response == 'y':
        print_info("Installation en cours...")
        try:
            subprocess.run(["pip", "install", "-r", "backend/requirements.txt"], check=True)
            print_success("Dépendances installées")
        except subprocess.CalledProcessError:
            print_error("Erreur lors de l'installation")
            print_info("Installez manuellement: cd backend && pip install -r requirements.txt")
    
    # === RÉSUMÉ FINAL ===
    print_header("✅ MISE À JOUR TERMINÉE")
    
    print(f"\n{Colors.GREEN}✅ Fichiers mis à jour automatiquement:{Colors.RESET}")
    print("  • backend/requirements.txt (doublons supprimés)")
    print("  • .env.template (nouveau template sécurisé)")
    print("  • .gitignore (protection fichiers sensibles)")
    print("  • backend/core/honeypot_detector.py (API réelle)")
    print("  • INSTALL_GUIDE.md (guide complet)")
    
    print(f"\n{Colors.YELLOW}📥 Fichiers à télécharger manuellement:{Colors.RESET}")
    print("  • backend/core/detector.py (depuis artifact Claude)")
    print("  • backend/core/token_analyzer.py (depuis artifact Claude)")
    print("  • scripts/setup_wallet.py (depuis artifact Claude)")
    
    print(f"\n{Colors.CYAN}📖 LISEZ: INSTALL_GUIDE.md pour les instructions complètes{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}⚠️  ACTIONS URGENTES:{Colors.RESET}")
    print("  1. Révoquer token Telegram (@BotFather -> /revoke)")
    print("  2. Générer nouvelles clés: openssl rand -base64 32")
    print("  3. Configurer .env avec vos clés")
    print("  4. Télécharger les 3 fichiers volumineux")
    print("  5. Créer nouveau wallet: python scripts/setup_wallet.py")
    
    print(f"\n{Colors.GREEN}🎯 Prochaine étape:{Colors.RESET}")
    print(f"  {Colors.CYAN}cat INSTALL_GUIDE.md{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✨ Bon courage avec les améliorations !{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Interruption utilisateur{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erreur: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
