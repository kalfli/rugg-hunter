#!/usr/bin/env python3
"""
🎯 RUG HUNTER BOT v4.0 - SCRIPT DE DÉMARRAGE
===========================================
Script simplifié pour lancer le bot
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Affiche le banner du bot"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║              🎯 RUG HUNTER BOT v4.0 - ULTIMATE                ║
║                                                                ║
║          Bot le plus complet pour détecter les tokens         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_python_version():
    """Vérifie la version de Python"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ requis!")
        print(f"   Version actuelle: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} détecté")

def check_dependencies():
    """Vérifie si les dépendances sont installées"""
    try:
        import fastapi
        import uvicorn
        import rich
        import web3
        print("✅ Dépendances principales installées")
        return True
    except ImportError as e:
        print(f"❌ Dépendances manquantes: {e}")
        print("\n📦 Installation des dépendances...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dépendances installées avec succès!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erreur lors de l'installation des dépendances")
            print("\n💡 Essayez manuellement:")
            print("   pip install -r requirements.txt")
            return False

def check_env_file():
    """Vérifie si le fichier .env existe"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  Fichier .env non trouvé")
        print("\n📝 Création du fichier .env...")
        
        env_content = """# RUG HUNTER BOT v4.0 - CONFIGURATION

# === MODE ===
TRADING_MODE=PAPER
AUTO_TRADING_ENABLED=false

# === BLOCKCHAINS ===
ETH_RPC_URL=https://eth.llamarpc.com
BSC_RPC_URL=https://bsc-dataseed.binance.org

# === WALLET (pour mode LIVE uniquement) ===
WALLET_PRIVATE_KEY=hen gasp fade trumpet senior kiss goat illegal ability alter feature shop
WALLET_ADDRESS=0x0300E57AEcfB8061F84074afE2582Cc82E38E38F

# === NOTIFICATIONS ===
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DISCORD_WEBHOOK_URL=

# === SCAN ===
SCAN_INTERVAL_SECONDS=15
MIN_LIQUIDITY_USD=5000
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("✅ Fichier .env créé!")
        print("💡 Éditez .env pour personnaliser la configuration")
    else:
        print("✅ Fichier .env trouvé")

def start_bot():
    """Démarre le bot"""
    print("\n" + "="*60)
    print("🚀 DÉMARRAGE DU BOT...")
    print("="*60)
    
    print("\n📊 Le bot va démarrer avec:")
    print("   • Mode: PAPER (simulation)")
    print("   • Auto-trading: DÉSACTIVÉ")
    print("   • Scan: Toutes les 15 secondes")
    print("   • Dashboard: http://localhost:8000")
    print("   • API: http://localhost:8000/api/health")
    
    print("\n" + "="*60)
    print("💡 COMMANDES UTILES:")
    print("="*60)
    print("   • Dashboard web: http://localhost:8000")
    print("   • Arrêt: Ctrl+C")
    print("   • Logs: Affichés en temps réel ci-dessous")
    print("="*60 + "\n")
    
    # Chercher le fichier main
    backend_path = Path("backend")
    
    if (backend_path / "main_ultimate.py").exists():
        main_file = backend_path / "main_ultimate.py"
    elif (backend_path / "main.py").exists():
        main_file = backend_path / "main.py"
    elif Path("main_ultimate.py").exists():
        main_file = Path("main_ultimate.py")
    else:
        print("❌ Fichier main non trouvé!")
        print("💡 Assurez-vous d'avoir:")
        print("   • backend/main_ultimate.py")
        print("   • OU backend/main.py")
        sys.exit(1)
    
    try:
        # Lancer le bot
        subprocess.run([sys.executable, str(main_file)])
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du bot...")
        print("✅ Bot arrêté avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)

def main():
    """Fonction principale"""
    print_banner()
    
    print("🔍 Vérifications préliminaires...\n")
    
    # Vérifications
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    check_env_file()
    
    print("\n✅ Toutes les vérifications passées!")
    
    # Demander confirmation
    print("\n" + "="*60)
    response = input("🚀 Voulez-vous démarrer le bot ? (o/N): ").strip().lower()
    
    if response in ['o', 'oui', 'y', 'yes']:
        start_bot()
    else:
        print("\n❌ Démarrage annulé")
        print("💡 Pour démarrer manuellement:")
        print("   python backend/main_ultimate.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)