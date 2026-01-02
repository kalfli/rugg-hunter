"""Automated Trading Execution System"""
import asyncio
import logging
from typing import Dict, Optional
from web3 import Web3
from eth_account import Account
import time

logger = logging.getLogger(__name__)

class AutoTrader:
    def __init__(self, trading_engine, wallet_manager, risk_manager, config: dict):
        self.engine = trading_engine
        self.wallet = wallet_manager
        self.risk = risk_manager
        self.config = config
        self.enabled = config.get("AUTO_TRADING_ENABLED", False)
        self.min_confidence = config.get("MIN_AUTO_TRADE_CONFIDENCE", 75)
        self.active_positions = {}
        self.trade_history = []
        
        if self.enabled:
            logger.info(f"✅ Auto-trading ENABLED (min confidence: {self.min_confidence}%)")
        else:
            logger.info("ℹ️ Auto-trading DISABLED (manual mode)")
    
    async def evaluate_and_execute(self, detection: dict, analysis: dict) -> Optional[dict]:
        """Évalue et exécute automatiquement un trade"""
        
        if not self.enabled:
            logger.info("Auto-trading disabled - skipping execution")
            return None
        
        recommendation = analysis['trading_recommendation']
        action = recommendation['action']
        final_score = analysis['final_score']
        
        # Vérifier si on doit trader
        if not self._should_auto_trade(action, final_score, recommendation):
            logger.info(f"Auto-trade criteria not met for {detection['symbol']}")
            return None
        
        # Vérifier les limites de risque
        risk_check = self.risk.check_circuit_breaker({})
        if risk_check['should_pause']:
            logger.warning("🛑 Circuit breaker active - no trading")
            return None
        
        # Exécuter le trade
        try:
            trade_result = await self._execute_buy_order(detection, recommendation, analysis)
            
            if trade_result and trade_result['success']:
                # Enregistrer la position
                position = self._create_position(detection, recommendation, trade_result)
                self.active_positions[position['position_id']] = position
                self.trade_history.append(trade_result)
                
                logger.info(f"✅ Auto-trade executed: {detection['symbol']} - Position ID: {position['position_id']}")
                
                # Démarrer le monitoring de la position
                asyncio.create_task(self._monitor_position(position, recommendation))
                
                return trade_result
            
        except Exception as e:
            logger.error(f"❌ Auto-trade execution failed: {e}")
            return None
    
    def _should_auto_trade(self, action: str, final_score: dict, recommendation: dict) -> bool:
        """Détermine si on doit auto-trader"""
        
        # Seulement pour les actions BUY
        if action not in ["BUY_AGGRESSIVE", "BUY_MODERATE", "BUY_CAUTIOUS"]:
            return False
        
        # Vérifier la confiance
        confidence = final_score['confidence']
        if confidence < self.min_confidence:
            logger.info(f"Confidence too low: {confidence}% < {self.min_confidence}%")
            return False
        
        # Vérifier le score global
        if final_score['overall_score'] < 60:
            logger.info(f"Overall score too low: {final_score['overall_score']}")
            return False
        
        # Vérifier la sécurité
        if final_score['security_score'] < 70:
            logger.info(f"Security score too low: {final_score['security_score']}")
            return False
        
        return True
    
    async def _execute_buy_order(self, detection: dict, recommendation: dict, analysis: dict) -> dict:
        """Exécute l'ordre d'achat"""
        
        position_sizing = recommendation['position_sizing']
        entry = recommendation['entry']
        
        logger.info(f"🤖 Executing auto-trade for {detection['symbol']}")
        logger.info(f" Amount: {position_sizing['amount_eth']} ETH")
        logger.info(f" Target Price: ${entry['price_target']:.10f}")
        
        # Exécution via le trading engine
        result = await self.engine.execute_buy(
            token_address=detection['token_address'],
            chain=detection['chain'],
            amount_eth=position_sizing['amount_eth'],
            slippage_percent=float(position_sizing['max_slippage'].split('-')[1].replace('%', '')),
            strategy="auto_trade"
        )
        
        return result
    
    def _create_position(self, detection: dict, recommendation: dict, trade_result: dict) -> dict:
        """Crée un objet position"""
        
        stop_loss = recommendation['stop_loss']
        exit_strategy = recommendation['exit_strategy']
        
        position = {
            "position_id": trade_result['position_id'],
            "token_address": detection['token_address'],
            "symbol": detection['symbol'],
            "chain": detection['chain'],
            "entry_price": trade_result['entry_price'],
            "amount_eth": recommendation['position_sizing']['amount_eth'],
            "amount_tokens": trade_result['tokens_received'],
            "entry_time": time.time(),
            "stop_loss_price": stop_loss['price'],
            "stop_loss_percent": stop_loss['percent'],
            "exit_strategy": exit_strategy,
            "status": "ACTIVE",
            "pnl_percent": 0,
            "pnl_usd": 0,
            "recommendation": recommendation
        }
        
        return position
    
    async def _monitor_position(self, position: dict, recommendation: dict):
        """Surveille une position active"""
        
        logger.info(f"👁️ Starting position monitoring: {position['symbol']}")
        
        while position['status'] == "ACTIVE":
            try:
                await asyncio.sleep(30) # Check toutes les 30 secondes
                
                # Récupérer le prix actuel (simulation pour l'instant)
                current_price = position['entry_price'] * 1.05 # Simulation
                
                # Calculer PnL
                pnl_percent = ((current_price - position['entry_price']) / position['entry_price']) * 100
                position['pnl_percent'] = pnl_percent
                
                logger.info(f"📊 {position['symbol']}: PnL = {pnl_percent:+.2f}%")
                
                # Vérifier stop loss
                if current_price <= position['stop_loss_price']:
                    logger.warning(f"🛑 Stop loss hit for {position['symbol']}")
                    await self._execute_sell(position, 100, "STOP_LOSS")
                    break
                
                # Vérifier take profits
                for i, tp in enumerate(position['exit_strategy']):
                    if current_price >= tp['price'] and not tp.get('executed'):
                        logger.info(f"🎯 Take profit {i+1} hit for {position['symbol']}")
                        await self._execute_sell(position, tp['sell_percent'], tp['level'])
                        tp['executed'] = True
                        
                        # Si tout vendu
                        if sum(tp.get('executed', False) for tp in position['exit_strategy']) == len(position['exit_strategy']):
                            position['status'] = "CLOSED"
                            break
                
            except Exception as e:
                logger.error(f"❌ Error monitoring position: {e}")
                await asyncio.sleep(60)
    
    async def _execute_sell(self, position: dict, percentage: int, reason: str):
        """Exécute un ordre de vente"""
        
        logger.info(f"💰 Executing sell order: {position['symbol']} - {percentage}% - Reason: {reason}")
        
        result = await self.engine.execute_sell(
            position_id=position['position_id'],
            percentage=percentage,
            reason=reason
        )
        
        if result['success']:
            logger.info(f"✅ Sell executed: PnL = {result['pnl_realized_percent']:+.2f}%")
            
            if percentage >= 100:
                position['status'] = "CLOSED"
                position['exit_time'] = time.time()
                position['final_pnl_percent'] = result['pnl_realized_percent']
                position['final_pnl_usd'] = result['pnl_realized_usd']
        
        return result
    
    def get_active_positions(self) -> list:
        """Retourne les positions actives"""
        return [p for p in self.active_positions.values() if p['status'] == "ACTIVE"]
    
    def get_trade_history(self, limit: int = 50) -> list:
        """Retourne l'historique des trades"""
        return self.trade_history[-limit:]
    
    def get_statistics(self) -> dict:
        """Statistiques de trading"""
        total_trades = len(self.trade_history)
        
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0
            }
        
        closed_positions = [p for p in self.active_positions.values() if p['status'] == "CLOSED"]
        winning_trades = sum(1 for p in closed_positions if p.get('final_pnl_percent', 0) > 0)
        total_pnl = sum(p.get('final_pnl_usd', 0) for p in closed_positions)
        
        return {
            "total_trades": total_trades,
            "active_positions": len(self.get_active_positions()),
            "closed_positions": len(closed_positions),
            "winning_trades": winning_trades,
            "losing_trades": len(closed_positions) - winning_trades,
            "win_rate": (winning_trades / len(closed_positions) * 100) if closed_positions else 0,
            "total_pnl_usd": total_pnl,
            "avg_pnl_usd": total_pnl / len(closed_positions) if closed_positions else 0
        }
