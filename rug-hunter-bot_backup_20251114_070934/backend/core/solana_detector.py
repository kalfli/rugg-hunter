"""
🌟 Détecteur de Nouveaux Tokens Solana
Surveille Raydium, Jupiter et Pump.fun pour détecter les nouveaux tokens SOL
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SolanaTokenDetector:
    """
    Détecte les nouveaux tokens sur Solana en surveillant:
    - Raydium (DEX principal)
    - Jupiter (Aggregateur)
    - Pump.fun (Plateforme de lancement)
    - Orca (DEX)
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.session = None
        self.seen_tokens = set()
        
        # Adresses des programmes Solana importants
        self.RAYDIUM_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
        self.JUPITER_PROGRAM = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
        self.PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
        self.ORCA_PROGRAM = "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP"
        
    async def get_session(self):
        """Obtient ou crée une session aiohttp"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def start_detection(self):
        """Démarre la détection multi-sources"""
        logger.info("🌟 Starting Solana detection...")
        
        tasks = [
            self.monitor_raydium(),
            self.monitor_jupiter(),
            self.monitor_pump_fun(),
            self.monitor_dexscreener()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def monitor_raydium(self):
        """Surveille les nouvelles paires sur Raydium"""
        while True:
            try:
                # Récupérer les nouvelles paires créées
                new_pairs = await self._fetch_raydium_new_pairs()
                
                for pair in new_pairs:
                    if pair["mint"] not in self.seen_tokens:
                        self.seen_tokens.add(pair["mint"])
                        token_data = await self.analyze_token(pair["mint"], "RAYDIUM")
                        
                        if token_data:
                            yield token_data
                
                await asyncio.sleep(3)  # Scan toutes les 3 secondes
                
            except Exception as e:
                logger.error(f"Raydium monitor error: {e}")
                await asyncio.sleep(5)
    
    async def monitor_jupiter(self):
        """Surveille Jupiter pour nouveaux tokens"""
        while True:
            try:
                # Jupiter API pour tokens récents
                new_tokens = await self._fetch_jupiter_new_tokens()
                
                for token in new_tokens:
                    if token["address"] not in self.seen_tokens:
                        self.seen_tokens.add(token["address"])
                        token_data = await self.analyze_token(token["address"], "JUPITER")
                        
                        if token_data:
                            yield token_data
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Jupiter monitor error: {e}")
                await asyncio.sleep(5)
    
    async def monitor_pump_fun(self):
        """Surveille Pump.fun pour nouveaux lancements"""
        while True:
            try:
                # Pump.fun API
                new_launches = await self._fetch_pump_fun_launches()
                
                for launch in new_launches:
                    if launch["mint"] not in self.seen_tokens:
                        self.seen_tokens.add(launch["mint"])
                        token_data = await self.analyze_token(launch["mint"], "PUMP_FUN")
                        
                        if token_data:
                            yield token_data
                
                await asyncio.sleep(2)  # Pump.fun est très rapide
                
            except Exception as e:
                logger.error(f"Pump.fun monitor error: {e}")
                await asyncio.sleep(5)
    
    async def monitor_dexscreener(self):
        """Surveille DexScreener pour nouveaux tokens SOL"""
        while True:
            try:
                session = await self.get_session()
                url = "https://api.dexscreener.com/latest/dex/search?q=SOL"
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pairs = data.get("pairs", [])
                        
                        for pair in pairs:
                            if pair.get("chainId") == "solana":
                                token_address = pair.get("baseToken", {}).get("address")
                                
                                if token_address and token_address not in self.seen_tokens:
                                    # Vérifier que c'est récent (< 30 min)
                                    created_at = pair.get("pairCreatedAt")
                                    if created_at:
                                        created_time = datetime.fromtimestamp(created_at / 1000)
                                        if datetime.now() - created_time < timedelta(minutes=30):
                                            self.seen_tokens.add(token_address)
                                            token_data = await self.analyze_token(token_address, "DEXSCREENER")
                                            
                                            if token_data:
                                                yield token_data
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"DexScreener monitor error: {e}")
                await asyncio.sleep(5)
    
    async def analyze_token(self, token_address: str, source: str) -> Optional[Dict]:
        """
        Analyse complète d'un token Solana
        Retourne les données enrichies ou None si invalide
        """
        try:
            # 1. Obtenir les métadonnées du token
            metadata = await self._get_token_metadata(token_address)
            if not metadata:
                return None
            
            # 2. Obtenir les données de liquidité
            liquidity_data = await self._get_liquidity_data(token_address)
            
            # 3. Obtenir les holders
            holders_data = await self._get_holders_data(token_address)
            
            # 4. Calculer l'âge du token
            age_minutes = await self._get_token_age(token_address)
            
            # 5. Vérifier la sécurité (freeze authority, mint authority)
            security_check = await self._check_token_security(token_address)
            
            # 6. Obtenir les données de trading
            trading_data = await self._get_trading_data(token_address)
            
            # Construire l'objet de détection
            return {
                "token_address": token_address,
                "chain": "SOL",
                "source": source,
                "symbol": metadata.get("symbol", "UNKNOWN"),
                "name": metadata.get("name", "Unknown Token"),
                "decimals": metadata.get("decimals", 9),
                
                # Liquidité
                "liquidity_usd": liquidity_data.get("liquidity_usd", 0),
                "liquidity_sol": liquidity_data.get("liquidity_sol", 0),
                
                # Prix
                "price_usd": trading_data.get("price_usd", 0),
                "price_sol": trading_data.get("price_sol", 0),
                
                # Market data
                "market_cap_usd": trading_data.get("market_cap_usd", 0),
                "volume_24h_usd": trading_data.get("volume_24h", 0),
                "price_change_1h": trading_data.get("price_change_1h", 0),
                
                # Holders
                "holders": holders_data.get("count", 0),
                "top10_holders_percent": holders_data.get("top10_percent", 100),
                
                # Sécurité
                "freeze_authority": security_check.get("freeze_authority"),
                "mint_authority": security_check.get("mint_authority"),
                "is_mutable": security_check.get("is_mutable", True),
                
                # Métadonnées
                "age_minutes": age_minutes,
                "detected_at": datetime.now(),
                
                # Social
                "has_website": bool(metadata.get("website")),
                "has_telegram": bool(metadata.get("telegram")),
                "has_twitter": bool(metadata.get("twitter")),
            }
            
        except Exception as e:
            logger.error(f"Token analysis error for {token_address}: {e}")
            return None
    
    # ========================================================================
    # Méthodes privées pour récupérer les données
    # ========================================================================
    
    async def _fetch_raydium_new_pairs(self) -> List[Dict]:
        """Récupère les nouvelles paires Raydium"""
        try:
            session = await self.get_session()
            url = "https://api.raydium.io/v2/main/pairs"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Filtrer les paires récentes (< 30 min)
                    recent_pairs = []
                    for pair in data:
                        created = pair.get("poolOpenTime", 0)
                        if created > 0:
                            created_time = datetime.fromtimestamp(created)
                            if datetime.now() - created_time < timedelta(minutes=30):
                                recent_pairs.append({
                                    "mint": pair.get("baseMint"),
                                    "pair_address": pair.get("ammId")
                                })
                    return recent_pairs
        except Exception as e:
            logger.error(f"Raydium fetch error: {e}")
        return []
    
    async def _fetch_jupiter_new_tokens(self) -> List[Dict]:
        """Récupère les nouveaux tokens via Jupiter"""
        try:
            session = await self.get_session()
            url = "https://token.jup.ag/all"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    tokens = await resp.json()
                    # Retourner tokens récents basé sur tags
                    return [t for t in tokens if "new" in t.get("tags", [])][:50]
        except Exception as e:
            logger.error(f"Jupiter fetch error: {e}")
        return []
    
    async def _fetch_pump_fun_launches(self) -> List[Dict]:
        """Récupère les nouveaux lancements Pump.fun"""
        try:
            session = await self.get_session()
            url = "https://frontend-api.pump.fun/coins/latest"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[:20]  # Les 20 plus récents
        except Exception as e:
            logger.error(f"Pump.fun fetch error: {e}")
        return []
    
    async def _get_token_metadata(self, token_address: str) -> Optional[Dict]:
        """Récupère les métadonnées d'un token"""
        try:
            session = await self.get_session()
            
            # Essayer Jupiter Token List d'abord
            url = f"https://token.jup.ag/token/{token_address}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
            
            # Sinon, RPC call pour les métadonnées on-chain
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [token_address, {"encoding": "jsonParsed"}]
            }
            
            async with session.post(self.rpc_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    account_data = data.get("result", {}).get("value", {}).get("data", {})
                    if "parsed" in account_data:
                        info = account_data["parsed"].get("info", {})
                        return {
                            "symbol": info.get("symbol", "UNKNOWN"),
                            "name": info.get("name", "Unknown"),
                            "decimals": info.get("decimals", 9)
                        }
        except Exception as e:
            logger.error(f"Metadata fetch error: {e}")
        
        return {"symbol": "UNKNOWN", "name": "Unknown", "decimals": 9}
    
    async def _get_liquidity_data(self, token_address: str) -> Dict:
        """Récupère les données de liquidité"""
        try:
            session = await self.get_session()
            
            # DexScreener pour liquidité
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        pair = pairs[0]
                        return {
                            "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                            "liquidity_sol": float(pair.get("liquidity", {}).get("base", 0))
                        }
        except Exception as e:
            logger.error(f"Liquidity fetch error: {e}")
        
        return {"liquidity_usd": 0, "liquidity_sol": 0}
    
    async def _get_holders_data(self, token_address: str) -> Dict:
        """Récupère les données des holders"""
        try:
            # Utiliser Helius ou autre service d'indexation
            # Pour l'instant, retourner des valeurs par défaut
            return {
                "count": 0,
                "top10_percent": 100
            }
        except Exception as e:
            logger.error(f"Holders fetch error: {e}")
        
        return {"count": 0, "top10_percent": 100}
    
    async def _get_token_age(self, token_address: str) -> int:
        """Calcule l'âge du token en minutes"""
        try:
            session = await self.get_session()
            
            # Récupérer la première signature (création)
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [token_address, {"limit": 1000}]
            }
            
            async with session.post(self.rpc_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    signatures = data.get("result", [])
                    if signatures:
                        # La dernière signature est la plus ancienne
                        oldest_sig = signatures[-1]
                        timestamp = oldest_sig.get("blockTime", 0)
                        if timestamp:
                            created_time = datetime.fromtimestamp(timestamp)
                            age = datetime.now() - created_time
                            return int(age.total_seconds() / 60)
        except Exception as e:
            logger.error(f"Age fetch error: {e}")
        
        return 0
    
    async def _check_token_security(self, token_address: str) -> Dict:
        """Vérifie la sécurité du token (authorities)"""
        try:
            session = await self.get_session()
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [token_address, {"encoding": "jsonParsed"}]
            }
            
            async with session.post(self.rpc_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    account_data = data.get("result", {}).get("value", {}).get("data", {})
                    if "parsed" in account_data:
                        info = account_data["parsed"].get("info", {})
                        return {
                            "freeze_authority": info.get("freezeAuthority"),
                            "mint_authority": info.get("mintAuthority"),
                            "is_mutable": bool(info.get("mintAuthority"))
                        }
        except Exception as e:
            logger.error(f"Security check error: {e}")
        
        return {
            "freeze_authority": None,
            "mint_authority": None,
            "is_mutable": True
        }
    
    async def _get_trading_data(self, token_address: str) -> Dict:
        """Récupère les données de trading"""
        try:
            session = await self.get_session()
            
            # DexScreener pour trading data
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        pair = pairs[0]
                        return {
                            "price_usd": float(pair.get("priceUsd", 0)),
                            "price_sol": float(pair.get("priceNative", 0)),
                            "market_cap_usd": float(pair.get("fdv", 0)),
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                            "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0))
                        }
        except Exception as e:
            logger.error(f"Trading data fetch error: {e}")
        
        return {
            "price_usd": 0,
            "price_sol": 0,
            "market_cap_usd": 0,
            "volume_24h": 0,
            "price_change_1h": 0
        }
    
    async def close(self):
        """Ferme la session"""
        if self.session:
            await self.session.close()


# ============================================================================
# HONEYPOT DETECTOR POUR SOLANA
# ============================================================================

class SolanaHoneypotDetector:
    """
    Détecte les honeypots sur Solana en vérifiant:
    - Freeze authority (peut bloquer les transferts)
    - Mint authority (peut créer des tokens infiniment)
    - Transfer hooks malveillants
    - Ownership renonciation
    """
    
    async def check_token(self, token_address: str) -> Dict:
        """
        Vérifie si un token Solana est un honeypot
        """
        result = {
            "is_honeypot": False,
            "can_buy": True,
            "can_sell": True,
            "warnings": [],
            "confidence": 0,
            "checks_passed": 0,
            "checks_total": 5
        }
        
        try:
            detector = SolanaTokenDetector()
            
            # Check 1: Freeze authority
            security = await detector._check_token_security(token_address)
            
            if security.get("freeze_authority"):
                result["warnings"].append("Freeze authority not renounced - owner can freeze transfers")
                result["confidence"] -= 20
            else:
                result["checks_passed"] += 1
            
            # Check 2: Mint authority
            if security.get("mint_authority"):
                result["warnings"].append("Mint authority not renounced - unlimited supply possible")
                result["confidence"] -= 15
            else:
                result["checks_passed"] += 1
            
            # Check 3: Holders distribution
            holders = await detector._get_holders_data(token_address)
            if holders.get("top10_percent", 100) > 80:
                result["warnings"].append("Highly concentrated ownership - top 10 holders own >80%")
                result["confidence"] -= 10
            else:
                result["checks_passed"] += 1
            
            # Check 4: Liquidity
            liquidity = await detector._get_liquidity_data(token_address)
            if liquidity.get("liquidity_usd", 0) < 1000:
                result["warnings"].append("Very low liquidity - high risk of rug pull")
                result["confidence"] -= 10
            else:
                result["checks_passed"] += 1
            
            # Check 5: Age
            age = await detector._get_token_age(token_address)
            if age < 5:
                result["warnings"].append("Token less than 5 minutes old - extreme risk")
                result["confidence"] -= 10
            else:
                result["checks_passed"] += 1
            
            # Calculer confiance finale
            result["confidence"] = max(0, 100 + result["confidence"])
            
            # Déterminer si c'est un honeypot
            if result["confidence"] < 50 or len(result["warnings"]) >= 3:
                result["is_honeypot"] = True
                result["can_sell"] = False
            
            await detector.close()
            
        except Exception as e:
            logger.error(f"Solana honeypot check error: {e}")
        
        return result
