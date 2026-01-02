"""Advanced Honeypot Detector - VERSION CORRIGÉE"""
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
