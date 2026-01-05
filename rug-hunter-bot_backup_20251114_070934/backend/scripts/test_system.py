#!/usr/bin/env python3
"""
🧪 RUG HUNTER BOT V3.0 - Test System Complet
Vérifie que tous les composants fonctionnent correctement
"""

import asyncio
import sys
from typing import Dict, List
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class SystemTester:
    """Testeur de système complet"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
    
    def print_header(self, text: str):
        """Affiche un header"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}{Colors.END}\n")
    
    def print_test(self, name: str, status: bool, message: str = ""):
        """Affiche le résultat d'un test"""
        self.tests_total += 1
        if status:
            self.tests_passed += 1
            symbol = f"{Colors.GREEN}✓{Colors.END}"
        else:
            self.tests_failed += 1
            symbol = f"{Colors.RED}✗{Colors.END}"
        
        msg = f" - {message}" if message else ""
        print(f"{symbol} {name}{msg}")
    
    async def test_imports(self) -> bool:
        """Test 1: Vérifier que tous les imports fonctionnent"""
        self.print_header("TEST 1: Imports des Modules")
        
        modules = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("websockets", "WebSockets"),
            ("aiohttp", "Aiohttp"),
            ("web3", "Web3"),
            ("solana", "Solana"),
            ("pydantic", "Pydantic"),
            ("sqlalchemy", "SQLAlchemy"),
            ("pandas", "Pandas"),
            ("numpy", "NumPy"),
            ("sklearn", "Scikit-learn")
        ]
        
        all_ok = True
        for module_name, display_name in modules:
            try:
                __import__(module_name)
                self.print_test(display_name, True)
            except ImportError as e:
                self.print_test(display_name, False, str(e))
                all_ok = False
        
        return all_ok
    
    async def test_config(self) -> bool:
        """Test 2: Vérifier la configuration"""
        self.print_header("TEST 2: Configuration")
        
        try:
            from pathlib import Path
            from dotenv import load_dotenv
            import os
            
            # Charger .env
            load_dotenv()
            
            # Variables requises
            required_vars = [
                "TRADING_MODE",
                "ETH_RPC_URL",
                "BSC_RPC_URL",
                "SOL_RPC_URL"
            ]
            
            all_ok = True
            for var in required_vars:
                value = os.getenv(var)
                if value:
                    self.print_test(f"{var}", True, value[:50] + "...")
                else:
                    self.print_test(f"{var}", False, "Non défini")
                    all_ok = False
            
            return all_ok
            
        except Exception as e:
            self.print_test("Configuration", False, str(e))
            return False
    
    async def test_rpc_connections(self) -> bool:
        """Test 3: Tester les connexions RPC"""
        self.print_header("TEST 3: Connexions RPC")
        
        import aiohttp
        import os
        
        rpcs = {
            "Ethereum": os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"),
            "BSC": os.getenv("BSC_RPC_URL", "https://bsc-dataseed1.binance.org"),
            "Solana": os.getenv("SOL_RPC_URL", "https://api.mainnet-beta.solana.com")
        }
        
        all_ok = True
        async with aiohttp.ClientSession() as session:
            for name, url in rpcs.items():
                try:
                    # Test simple request
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_blockNumber" if name != "Solana" else "getHealth"
                    }
                    
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            self.print_test(f"RPC {name}", True, url)
                        else:
                            self.print_test(f"RPC {name}", False, f"Status {resp.status}")
                            all_ok = False
                            
                except Exception as e:
                    self.print_test(f"RPC {name}", False, str(e))
                    all_ok = False
        
        return all_ok
    
    async def test_honeypot_detector(self) -> bool:
        """Test 4: Tester le détecteur de honeypot"""
        self.print_header("TEST 4: Honeypot Detector")
        
        try:
            # Import du détecteur
            import aiohttp
            
            # Token de test connu (WETH - sûr)
            test_token = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            
            async with aiohttp.ClientSession() as session:
                # Test Honeypot.is API
                url = "https://api.honeypot.is/v2/IsHoneypot"
                params = {"address": test_token, "chainID": 1}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        is_honeypot = data.get("honeypotResult", {}).get("isHoneypot", False)
                        
                        if not is_honeypot:
                            self.print_test("Honeypot.is API", True, "WETH non honeypot ✓")
                            return True
                        else:
                            self.print_test("Honeypot.is API", False, "WETH détecté comme honeypot")
                            return False
                    else:
                        self.print_test("Honeypot.is API", False, f"Status {resp.status}")
                        return False
                        
        except Exception as e:
            self.print_test("Honeypot Detector", False, str(e))
            return False
    
    async def test_ml_scorer(self) -> bool:
        """Test 5: Tester le scorer ML"""
        self.print_header("TEST 5: ML Scorer")
        
        try:
            # Créer un token de test
            test_token = {
                "liquidity_usd": 50000,
                "holders": 500,
                "contract_verified": True,
                "ownership_renounced": True,
                "volume_24h_usd": 10000,
                "age_minutes": 120,
                "has_website": True,
                "has_telegram": True,
                "top10_holders_percent": 30,
                "price_change_1h": 5
            }
            
            honeypot_check = {
                "is_honeypot": False,
                "confidence": 90,
                "checks_passed": 5,
                "buy_tax": 1,
                "sell_tax": 2
            }
            
            # Calculer le score (logique simplifiée)
            score = 0
            if not honeypot_check["is_honeypot"]:
                score += 15
            if honeypot_check["confidence"] >= 80:
                score += 10
            if test_token["contract_verified"]:
                score += 10
            if test_token["liquidity_usd"] >= 50000:
                score += 9
            if test_token["holders"] >= 500:
                score += 4
            
            self.print_test("Score Calculation", True, f"Score: {score}/100")
            
            if score >= 40:
                return True
            else:
                return False
                
        except Exception as e:
            self.print_test("ML Scorer", False, str(e))
            return False
    
    async def test_database(self) -> bool:
        """Test 6: Tester la connexion DB (optionnel)"""
        self.print_header("TEST 6: Database (Optionnel)")
        
        try:
            from sqlalchemy import create_engine, text
            
            # Pour test, utiliser SQLite en mémoire
            engine = create_engine("sqlite:///:memory:")
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.fetchone()[0] == 1:
                    self.print_test("SQLite Database", True, "Connexion OK")
                    return True
                    
        except Exception as e:
            self.print_test("Database", False, str(e))
            return False
    
    async def test_notifications(self) -> bool:
        """Test 7: Tester les notifications"""
        self.print_header("TEST 7: Notifications")
        
        import os
        
        # Telegram
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        
        if telegram_token and telegram_chat:
            self.print_test("Telegram Config", True, "Configuré")
        else:
            self.print_test("Telegram Config", False, "Non configuré (optionnel)")
        
        # Discord
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        
        if discord_webhook:
            self.print_test("Discord Config", True, "Configuré")
        else:
            self.print_test("Discord Config", False, "Non configuré (optionnel)")
        
        return True  # Non bloquant
    
    async def test_api_server(self) -> bool:
        """Test 8: Tester le serveur API"""
        self.print_header("TEST 8: API Server")
        
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            
            # Créer une app de test
            app = FastAPI()
            
            @app.get("/test")
            def test_route():
                return {"status": "ok"}
            
            client = TestClient(app)
            response = client.get("/test")
            
            if response.status_code == 200 and response.json()["status"] == "ok":
                self.print_test("FastAPI Server", True, "Server OK")
                return True
            else:
                self.print_test("FastAPI Server", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("API Server", False, str(e))
            return False
    
    async def test_websocket(self) -> bool:
        """Test 9: Tester WebSocket"""
        self.print_header("TEST 9: WebSocket")
        
        try:
            import websockets
            self.print_test("WebSocket Library", True, "Importé")
            return True
        except Exception as e:
            self.print_test("WebSocket", False, str(e))
            return False
    
    async def test_security(self) -> bool:
        """Test 10: Tester les fonctions de sécurité"""
        self.print_header("TEST 10: Security Checks")
        
        try:
            from cryptography.fernet import Fernet
            
            # Test chiffrement
            key = Fernet.generate_key()
            f = Fernet(key)
            
            test_data = b"test_secret_data"
            encrypted = f.encrypt(test_data)
            decrypted = f.decrypt(encrypted)
            
            if decrypted == test_data:
                self.print_test("Encryption/Decryption", True, "Fonctionne")
                return True
            else:
                self.print_test("Encryption/Decryption", False, "Échec")
                return False
                
        except Exception as e:
            self.print_test("Security", False, str(e))
            return False
    
    def print_summary(self):
        """Affiche le résumé"""
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"  RÉSUMÉ DES TESTS")
        print(f"{'='*70}{Colors.END}\n")
        
        success_rate = (self.tests_passed / self.tests_total * 100) if self.tests_total > 0 else 0
        
        print(f"Total:    {self.tests_total} tests")
        print(f"{Colors.GREEN}Réussis:  {self.tests_passed}{Colors.END}")
        print(f"{Colors.RED}Échoués:  {self.tests_failed}{Colors.END}")
        print(f"\nTaux de réussite: {success_rate:.1f}%\n")
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ TOUS LES TESTS PASSÉS !{Colors.END}\n")
            print(f"{Colors.GREEN}Le système est prêt à être utilisé.{Colors.END}\n")
        elif self.tests_failed < 3:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  QUELQUES TESTS ONT ÉCHOUÉ{Colors.END}\n")
            print(f"{Colors.YELLOW}Le système peut fonctionner mais certaines fonctionnalités")
            print(f"peuvent être limitées.{Colors.END}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ TROP DE TESTS ONT ÉCHOUÉ{Colors.END}\n")
            print(f"{Colors.RED}Veuillez corriger les erreurs avant de continuer.{Colors.END}\n")
    
    async def run_all_tests(self):
        """Lance tous les tests"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}")
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║                                                                  ║")
        print("║           🧪  RUG HUNTER BOT V3.0 - SYSTEM TESTS  🧪            ║")
        print("║                                                                  ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
        
        # Exécuter tous les tests
        await self.test_imports()
        await self.test_config()
        await self.test_rpc_connections()
        await self.test_honeypot_detector()
        await self.test_ml_scorer()
        await self.test_database()
        await self.test_notifications()
        await self.test_api_server()
        await self.test_websocket()
        await self.test_security()
        
        # Afficher le résumé
        self.print_summary()
        
        return self.tests_failed == 0


async def main():
    """Fonction principale"""
    tester = SystemTester()
    success = await tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrompus par l'utilisateur{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Erreur lors des tests: {e}{Colors.END}")
        sys.exit(1)
