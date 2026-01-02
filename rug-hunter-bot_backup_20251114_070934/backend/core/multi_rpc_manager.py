"""Multi-RPC Manager with Automatic Failover"""
import asyncio
import logging
import time
from typing import List, Optional
from web3 import Web3

logger = logging.getLogger(__name__)

class RPCEndpoint:
    def __init__(self, url: str, name: str, priority: int = 0):
        self.url = url
        self.name = name
        self.priority = priority
        self.is_healthy = True
        self.consecutive_failures = 0
        self.total_requests = 0
        self.total_failures = 0
        self.avg_latency_ms = 0
        self.last_check = time.time()
        self.last_error = None
        
    def record_success(self, latency_ms: float):
        self.total_requests += 1
        self.consecutive_failures = 0
        self.is_healthy = True
        if self.avg_latency_ms == 0:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = (self.avg_latency_ms * 0.8) + (latency_ms * 0.2)
    
    def record_failure(self, error: str):
        self.total_requests += 1
        self.total_failures += 1
        self.consecutive_failures += 1
        self.last_error = error
        if self.consecutive_failures >= 3:
            self.is_healthy = False
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return ((self.total_requests - self.total_failures) / self.total_requests) * 100

class MultiRPCManager:
    def __init__(self, chain: str):
        self.chain = chain
        self.endpoints: List[RPCEndpoint] = []
        self.active_endpoint: Optional[RPCEndpoint] = None
        self.running = False
        
    def add_endpoint(self, url: str, name: str, priority: int = 0):
        endpoint = RPCEndpoint(url, name, priority)
        self.endpoints.append(endpoint)
        self.endpoints.sort(key=lambda e: e.priority, reverse=True)
        if not self.active_endpoint:
            self.active_endpoint = endpoint
        logger.info(f"➕ Added RPC: {name}")
        
    async def start(self):
        self.running = True
        logger.info(f"🏥 RPC manager started for {self.chain}")
        
    def get_web3(self) -> Web3:
        best = self._get_best_endpoint()
        if not best:
            logger.error("❌ No healthy RPC!")
            return self._get_fallback_web3()
        
        if best != self.active_endpoint:
            logger.info(f"🔄 Switching to: {best.name}")
            self.active_endpoint = best
        
        return Web3(Web3.HTTPProvider(best.url, request_kwargs={'timeout': 30}))
    
    async def execute_with_retry(self, func, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                start = time.time()
                w3 = self.get_web3()
                result = func(w3)
                latency = (time.time() - start) * 1000
                
                if self.active_endpoint:
                    self.active_endpoint.record_success(latency)
                
                return result
            except Exception as e:
                if self.active_endpoint:
                    self.active_endpoint.record_failure(str(e))
                
                logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}")
                self.active_endpoint = self._get_best_endpoint()
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        raise Exception("All RPC attempts failed")
    
    def _get_best_endpoint(self) -> Optional[RPCEndpoint]:
        healthy = [e for e in self.endpoints if e.is_healthy]
        if not healthy:
            for e in self.endpoints:
                e.is_healthy = True
                e.consecutive_failures = 0
            healthy = self.endpoints
        
        healthy.sort(key=lambda e: e.priority, reverse=True)
        return healthy[0] if healthy else None
    
    def _get_fallback_web3(self) -> Web3:
        fallback = {
            "ETH": "https://eth.llamarpc.com",
            "BSC": "https://bsc-dataseed1.binance.org"
        }
        url = fallback.get(self.chain, "https://eth.llamarpc.com")
        return Web3(Web3.HTTPProvider(url))
    
    def get_status(self) -> dict:
        return {
            "chain": self.chain,
            "active_endpoint": self.active_endpoint.name if self.active_endpoint else None,
            "endpoints": [
                {
                    "name": e.name,
                    "url": e.url,
                    "is_healthy": e.is_healthy,
                    "priority": e.priority,
                    "success_rate": f"{e.success_rate:.1f}%",
                    "avg_latency_ms": f"{e.avg_latency_ms:.0f}",
                    "total_requests": e.total_requests,
                    "consecutive_failures": e.consecutive_failures,
                    "last_error": e.last_error
                }
                for e in self.endpoints
            ]
        }
    
    def stop(self):
        self.running = False

def create_default_rpc_manager(chain: str) -> MultiRPCManager:
    manager = MultiRPCManager(chain)
    
    if chain == "ETH":
        manager.add_endpoint("https://eth.llamarpc.com", "LlamaRPC", priority=10)
        manager.add_endpoint("https://rpc.ankr.com/eth", "Ankr", priority=9)
        manager.add_endpoint("https://ethereum.publicnode.com", "PublicNode", priority=8)
    elif chain == "BSC":
        manager.add_endpoint("https://bsc-dataseed1.binance.org", "Binance", priority=10)
        manager.add_endpoint("https://rpc.ankr.com/bsc", "Ankr", priority=9)
        manager.add_endpoint("https://bsc.publicnode.com", "PublicNode", priority=8)
    
    return manager
