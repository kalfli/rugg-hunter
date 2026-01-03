#!/usr/bin/env python3
"""
🚀 RUG HUNTER BOT V3.0 - Script de Démarrage Automatisé
Lance le bot avec toutes les vérifications nécessaires
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple

# Codes couleur pour terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Affiche le banner du bot"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              🚀  RUG HUNTER BOT V3.0  🚀                         ║
║                                                                  ║
║              Multi-Chain Token Hunter                            ║
║              ETH | BSC | SOLANA                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{Colors.END}
    """
    print(banner)

def print_step(step: str, status: str = "info"):
    """Affiche une étape avec couleur"""
    colors = {
        "info": Colors.BLUE,
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED
    }
    symbols = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    color = colors.get(status, Colors.BLUE)
    symbol = symbols.get(status, "ℹ️")
    print(f"{color}{symbol}  {step}{Colors.END}")

def check_python_version() -> bool:
    """Vérifie la version de Python"""
    print_step("Vérification de la version Python...", "info")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_step(f"Python {version.major}.{version.minor}.{version.micro} ✓", "success")
        return True
    else:
        print_step(f"Python {version.major}.{version.minor} - Version 3.9+ requise!", "error")
        return False

def check_env_file() -> bool:
    """Vérifie l'existence du fichier .env"""
    print_step("Vérification du fichier .env...", "info")
    if Path(".env").exists():
        print_step("Fichier .env trouvé ✓", "success")
        return True
    else:
        print_step("Fichier .env manquant!", "error")
        print(f"\n{Colors.YELLOW}Créez un fichier .env avec la configuration suivante:{Colors.END}\n")
        print("""
TRADING_MODE=PAPER
ETH_RPC_URL=https://eth.llamarpc.com
BSC_RPC_URL=https://bsc-dataseed1.binance.org
SOL_RPC_URL=https://api.mainnet-beta.solana.com
ENABLE_ETH_DETECTION=True
ENABLE_BSC_DETECTION=True
ENABLE_SOL_DETECTION=True
MIN_LIQUIDITY_USD=5000
        """)
        return False

def check_dependencies() -> Tuple[bool, List[str]]:
    """Vérifie les dépendances Python"""
    print_step("Vérification des dépendances...", "info")
    
    required = [
        "fastapi", "uvicorn", "websockets", "aiohttp",
        "web3", "solana", "pydantic", "sqlalchemy"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if not missing:
        print_step(f"Toutes les dépendances installées ✓", "success")
        return True, []
    else:
        print_step(f"{len(missing)} dépendances manquantes", "warning")
        return False, missing

def install_dependencies():
    """Installe les dépendances manquantes"""
    print_step("Installation des dépendances...", "info")
    
    if not Path("requirements.txt").exists():
        print_step("requirements.txt manquant!", "error")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ])
        print_step("Dépendances installées ✓", "success")
        return True
    except subprocess.CalledProcessError as e:
        print_step(f"Erreur d'installation: {e}", "error")
        return False

def check_port(port: int = 8000) -> bool:
    """Vérifie si le port est disponible"""
    import socket
    print_step(f"Vérification du port {port}...", "info")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result != 0:
        print_step(f"Port {port} disponible ✓", "success")
        return True
    else:
        print_step(f"Port {port} déjà utilisé!", "warning")
        return False

def load_env_config() -> dict:
    """Charge la configuration depuis .env"""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        "trading_mode": os.getenv("TRADING_MODE", "PAPER"),
        "eth_detection": os.getenv("ENABLE_ETH_DETECTION", "True") == "True",
        "bsc_detection": os.getenv("ENABLE_BSC_DETECTION", "True") == "True",
        "sol_detection": os.getenv("ENABLE_SOL_DETECTION", "True") == "True",
        "auto_trading": os.getenv("AUTO_TRADING_ENABLED", "False") == "True",
        "min_liquidity": os.getenv("MIN_LIQUIDITY_USD", "5000"),
    }
    
    return config

def display_config(config: dict):
    """Affiche la configuration actuelle"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}📋 Configuration Actuelle:{Colors.END}\n")
    
    mode_color = Colors.YELLOW if config["trading_mode"] == "PAPER" else Colors.RED
    print(f"  Mode Trading:    {mode_color}{config['trading_mode']}{Colors.END}")
    print(f"  Détection ETH:   {'✅' if config['eth_detection'] else '❌'}")
    print(f"  Détection BSC:   {'✅' if config['bsc_detection'] else '❌'}")
    print(f"  Détection SOL:   {'✅' if config['sol_detection'] else '❌'}")
    print(f"  Auto-Trading:    {'✅' if config['auto_trading'] else '❌'}")
    print(f"  Liquidité Min:   ${config['min_liquidity']}")
    print()

def start_backend():
    """Démarre le serveur backend"""
    print_step("Démarrage du serveur backend...", "info")
    
    try:
        import uvicorn
        from backend.main_improved import app
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}🚀 Serveur démarré!{Colors.END}")
        print(f"{Colors.CYAN}📊 Dashboard: {Colors.END}http://localhost:8000")
        print(f"{Colors.CYAN}📡 API: {Colors.END}http://localhost:8000/docs")
        print(f"{Colors.CYAN}🔌 WebSocket: {Colors.END}ws://localhost:8000/ws/feed")
        print(f"\n{Colors.YELLOW}Appuyez sur Ctrl+C pour arrêter le bot{Colors.END}\n")
        
        uvicorn.run(
            "backend.main_improved:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}🛑 Arrêt du bot...{Colors.END}")
        print_step("Bot arrêté avec succès", "success")
    except Exception as e:
        print_step(f"Erreur de démarrage: {e}", "error")
        return False
    
    return True

def main():
    """Fonction principale"""
    print_banner()
    
    # Étape 1: Vérifier Python
    if not check_python_version():
        sys.exit(1)
    
    # Étape 2: Vérifier .env
    if not check_env_file():
        print(f"\n{Colors.RED}Configuration requise avant de continuer!{Colors.END}")
        sys.exit(1)
    
    # Étape 3: Vérifier les dépendances
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n{Colors.YELLOW}Installation des dépendances manquantes...{Colors.END}")
        response = input("Installer maintenant? (o/n): ")
        if response.lower() == 'o':
            if not install_dependencies():
                sys.exit(1)
        else:
            print(f"{Colors.RED}Installation annulée{Colors.END}")
            sys.exit(1)
    
    # Étape 4: Vérifier le port
    if not check_port():
        print(f"\n{Colors.YELLOW}Un autre processus utilise le port 8000{Colors.END}")
        response = input("Continuer quand même? (o/n): ")
        if response.lower() != 'o':
            sys.exit(1)
    
    # Étape 5: Charger la config
    config = load_env_config()
    display_config(config)
    
    # Étape 6: Avertissement mode LIVE
    if config["trading_mode"] == "LIVE":
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  AVERTISSEMENT - MODE LIVE ACTIVÉ  ⚠️{Colors.END}")
        print(f"{Colors.RED}Vous allez trader avec de VRAIS fonds!{Colors.END}")
        print(f"{Colors.RED}Risque de perte totale du capital{Colors.END}\n")
        
        response = input("Êtes-vous ABSOLUMENT SÛR? (tapez 'OUI' en majuscules): ")
        if response != "OUI":
            print(f"{Colors.YELLOW}Démarrage annulé - Mode sécurisé{Colors.END}")
            sys.exit(0)
    
    # Étape 7: Démarrer le bot
    print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
    time.sleep(1)
    
    if not start_backend():
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Programme interrompu par l'utilisateur{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Erreur fatale: {e}{Colors.END}")
        sys.exit(1)
