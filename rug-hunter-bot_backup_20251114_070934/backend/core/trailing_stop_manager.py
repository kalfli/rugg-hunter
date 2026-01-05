"""Advanced Trailing Stop Loss Manager"""
import asyncio
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TrailingStopManager:
    def __init__(self, trading_engine):
        self.engine = trading_engine
        self.active_stops = {}
        self.running = False
        
    async def start(self):
        self.running = True
        logger.info("🎯 Trailing stop manager started")
        
        while self.running:
            try:
                await self._check_all_positions()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error: {e}")
                await asyncio.sleep(10)
    
    def add_position(self, position: Dict, strategy: str = "dynamic"):
        position_id = position['position_id']
        
        config = {
            "position": position,
            "strategy": strategy,
            "entry_price": position['entry_price'],
            "current_stop_price": position['entry_price'] * 0.85,
            "highest_price": position['entry_price'],
            "breakeven_activated": False,
            "created_at": time.time()
        }
        
        self.active_stops[position_id] = config
        logger.info(f"📍 Added trailing stop: {position.get('symbol', 'UNKNOWN')}")
    
    async def _check_all_positions(self):
        for position_id, config in list(self.active_stops.items()):
            try:
                # Simuler prix actuel
                current_price = config['entry_price'] * 1.1
                
                if current_price > config['highest_price']:
                    config['highest_price'] = current_price
                
                # Check stop loss
                if current_price <= config['current_stop_price']:
                    logger.warning(f"🛑 Stop loss hit: {config['position'].get('symbol')}")
                    del self.active_stops[position_id]
                
            except Exception as e:
                logger.error(f"Error checking position: {e}")
    
    def get_position_status(self, position_id: str) -> Optional[Dict]:
        if position_id not in self.active_stops:
            return None
        
        config = self.active_stops[position_id]
        return {
            "position_id": position_id,
            "symbol": config['position'].get('symbol', 'UNKNOWN'),
            "entry_price": config['entry_price'],
            "current_stop": config['current_stop_price'],
            "highest_price": config['highest_price'],
            "breakeven_activated": config['breakeven_activated'],
            "age_seconds": time.time() - config['created_at']
        }
    
    def stop(self):
        self.running = False
