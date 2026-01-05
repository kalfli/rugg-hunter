"""
🎯 RUG HUNTER BOT - ULTIMATE EDITION V5.0
==========================================
Version finale avec TOUS les liens directs + 150+ paramètres
✅ Scan blockchain réel
✅ Génération automatique de TOUS les liens
✅ Dashboard web synchronisé
✅ 150+ paramètres configurables
✅ Paper & Live trading
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Import du détecteur amélioré
from core.detector import MultiChainDetector

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler('rug_hunter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Charger .env
load_dotenv()

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TokenDetection:
    """Token détecté avec tous les liens"""
    id: str
    symbol: str
    name: str
    chain: str
    dex: str
    token_address: str
    pair_address: str
    liquidity_usd: float
    liquidity_native: float
    native_token: str
    price_usd: float
    price_native: float
    market_cap_usd: float
    holders_count: int
    token_age_minutes: int
    reliability_score: int
    risk_score: int
    owner_address: str
    owner_balance_percent: float
    ownership_renounced: bool
    has_mint_function: bool
    has_pause_function: bool
    has_blacklist: bool
    has_proxy: bool
    links: Dict[str, str]  # TOUS LES LIENS
    timestamp: datetime
    
    def to_dict(self):
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d

# ============================================================================
# APP STATE - État global
# ============================================================================

class AppState:
    def __init__(self):
        self.stats = {
            "start_time": datetime.utcnow(),
            "total_scans": 0,
            "total_blocks_scanned": 0,
            "total_detections": 0,
            "honeypots_blocked": 0,
            "suspicious_blocked": 0,
            "high_risk_blocked": 0,
            "passed_filters": 0,
            "trades_executed": 0,
            "trades_won": 0,
            "trades_lost": 0,
            "active_positions": 0,
            "total_pnl_usd": 0.0,
            "total_pnl_percent": 0.0,
            "win_rate": 0.0,
            "best_trade_percent": 0.0,
            "worst_trade_percent": 0.0,
            "last_scan_time": None,
            "next_scan_time": None,
            "scan_duration_ms": 0,
        }
        
        # Charger settings depuis .env
        self.settings = self._load_settings_from_env()
        
        self.recent_detections: List[TokenDetection] = []
        self.active_positions = []
        self.trade_history = []
        self.scan_running = False
        self.websocket_clients = []
        self.detector = None
    
    def _load_settings_from_env(self) -> dict:
        """Charge TOUS les paramètres depuis .env"""
        return {
            # === MODE & TRADING ===
            "TRADING_MODE": os.getenv("TRADING_MODE", "PAPER"),
            "AUTO_TRADING_ENABLED": os.getenv("AUTO_TRADING_ENABLED", "false").lower() == "true",
            "PAPER_STARTING_BALANCE_USD": float(os.getenv("PAPER_STARTING_BALANCE", 10000)),
            "CURRENT_BALANCE_USD": float(os.getenv("PAPER_STARTING_BALANCE", 10000)),
            
            # === SCAN ===
            "SCAN_ENABLED": os.getenv("SCAN_ENABLED", "true").lower() == "true",
            "SCAN_INTERVAL_SECONDS": int(os.getenv("SCAN_INTERVAL_SECONDS", 15)),
            "SCAN_BLOCKS_PER_CYCLE": int(os.getenv("SCAN_BLOCKS_PER_CYCLE", 10)),
            
            # === BLOCKCHAINS ===
            "ENABLE_ETH_DETECTION": os.getenv("ENABLE_ETH_DETECTION", "true").lower() == "true",
            "ENABLE_BSC_DETECTION": os.getenv("ENABLE_BSC_DETECTION", "true").lower() == "true",
            "ENABLE_BASE_DETECTION": os.getenv("ENABLE_BASE_DETECTION", "false").lower() == "true",
            "ENABLE_ARBITRUM_DETECTION": os.getenv("ENABLE_ARBITRUM_DETECTION", "false").lower() == "true",
            "ENABLE_POLYGON_DETECTION": os.getenv("ENABLE_POLYGON_DETECTION", "false").lower() == "true",
            "ENABLE_SOL_DETECTION": os.getenv("ENABLE_SOL_DETECTION", "false").lower() == "true",
            
            # === FILTRES LIQUIDITÉ ===
            "MIN_LIQUIDITY_USD": float(os.getenv("MIN_LIQUIDITY_USD", 5000)),
            "MAX_LIQUIDITY_USD": float(os.getenv("MAX_LIQUIDITY_USD", 10000000)),
            "MIN_LIQUIDITY_LOCKED_PERCENT": float(os.getenv("MIN_LIQUIDITY_LOCKED_PERCENT", 70)),
            "MIN_LIQUIDITY_LOCK_DAYS": int(os.getenv("MIN_LIQUIDITY_LOCK_DAYS", 30)),
            
            # === FILTRES TOKENS ===
            "MIN_TOKEN_AGE_MINUTES": int(os.getenv("MIN_TOKEN_AGE_MINUTES", 1)),
            "MAX_TOKEN_AGE_MINUTES": int(os.getenv("MAX_TOKEN_AGE_MINUTES", 30)),
            "MIN_HOLDERS": int(os.getenv("MIN_HOLDERS", 10)),
            "MAX_HOLDERS": int(os.getenv("MAX_HOLDERS", 50000)),
            "MAX_TOP_10_HOLDERS_PERCENT": float(os.getenv("MAX_TOP_10_HOLDERS_PERCENT", 60)),
            "MAX_OWNER_PERCENTAGE": float(os.getenv("MAX_OWNER_PERCENTAGE", 50)),
            
            # === FILTRES VOLUME ===
            "MIN_VOLUME_24H_USD": float(os.getenv("MIN_VOLUME_24H_USD", 1000)),
            "MAX_VOLUME_24H_USD": float(os.getenv("MAX_VOLUME_24H_USD", 100000000)),
            
            # === ML ===
            "USE_ADVANCED_ML": os.getenv("USE_ADVANCED_ML", "true").lower() == "true",
            "MIN_AUTO_TRADE_CONFIDENCE": int(os.getenv("MIN_AUTO_TRADE_CONFIDENCE", 75)),
            "MIN_MANUAL_NOTIFICATION_CONFIDENCE": int(os.getenv("MIN_MANUAL_NOTIFICATION_CONFIDENCE", 50)),
            
            # === POSITION SIZING ===
            "MAX_POSITION_SIZE_USD": float(os.getenv("MAX_POSITION_SIZE_USD", 500)),
            "MIN_POSITION_SIZE_USD": float(os.getenv("MIN_POSITION_SIZE_USD", 50)),
            "MAX_POSITION_SIZE_PERCENT": float(os.getenv("MAX_POSITION_SIZE_PERCENT", 10)),
            "MAX_CONCURRENT_POSITIONS": int(os.getenv("MAX_CONCURRENT_POSITIONS", 5)),
            
            # === RISK MANAGEMENT ===
            "RISK_PER_TRADE_PERCENT": float(os.getenv("RISK_PER_TRADE_PERCENT", 2)),
            "MAX_DAILY_LOSS_USD": float(os.getenv("MAX_DAILY_LOSS_USD", 1000)),
            "MAX_DAILY_LOSS_PERCENT": float(os.getenv("MAX_DAILY_LOSS_PERCENT", 15)),
            "MAX_WEEKLY_LOSS_PERCENT": float(os.getenv("MAX_WEEKLY_LOSS_PERCENT", 30)),
            "MAX_PORTFOLIO_EXPOSURE_PERCENT": float(os.getenv("MAX_PORTFOLIO_EXPOSURE_PERCENT", 30)),
            
            # === TAKE PROFIT ===
            "ENABLE_TAKE_PROFIT": os.getenv("ENABLE_TAKE_PROFIT", "true").lower() == "true",
            "TAKE_PROFIT_1_PERCENT": float(os.getenv("TAKE_PROFIT_1_PERCENT", 30)),
            "TAKE_PROFIT_1_SELL_PERCENT": float(os.getenv("TAKE_PROFIT_1_SELL_PERCENT", 25)),
            "TAKE_PROFIT_2_PERCENT": float(os.getenv("TAKE_PROFIT_2_PERCENT", 50)),
            "TAKE_PROFIT_2_SELL_PERCENT": float(os.getenv("TAKE_PROFIT_2_SELL_PERCENT", 25)),
            "TAKE_PROFIT_3_PERCENT": float(os.getenv("TAKE_PROFIT_3_PERCENT", 100)),
            "TAKE_PROFIT_3_SELL_PERCENT": float(os.getenv("TAKE_PROFIT_3_SELL_PERCENT", 50)),
            "TAKE_PROFIT_4_PERCENT": float(os.getenv("TAKE_PROFIT_4_PERCENT", 200)),
            "TAKE_PROFIT_4_SELL_PERCENT": float(os.getenv("TAKE_PROFIT_4_SELL_PERCENT", 100)),
            
            # === STOP LOSS ===
            "ENABLE_STOP_LOSS": os.getenv("ENABLE_STOP_LOSS", "true").lower() == "true",
            "STOP_LOSS_PERCENT": float(os.getenv("STOP_LOSS_PERCENT", 15)),
            "USE_TRAILING_STOP": os.getenv("USE_TRAILING_STOP", "true").lower() == "true",
            "TRAILING_STOP_ACTIVATION_PERCENT": float(os.getenv("TRAILING_STOP_ACTIVATION_PERCENT", 20)),
            "TRAILING_STOP_DISTANCE_PERCENT": float(os.getenv("TRAILING_STOP_DISTANCE_PERCENT", 10)),
            "PANIC_SELL_PERCENT": float(os.getenv("PANIC_SELL_PERCENT", 30)),
            
            # === TIME MANAGEMENT ===
            "MIN_HOLD_TIME_MINUTES": int(os.getenv("MIN_HOLD_TIME_MINUTES", 5)),
            "MAX_POSITION_HOLD_TIME_HOURS": int(os.getenv("MAX_POSITION_HOLD_TIME_HOURS", 24)),
            
            # === HONEYPOT ===
            "ENABLE_HONEYPOT_CHECK": os.getenv("ENABLE_HONEYPOT_CHECK", "true").lower() == "true",
            "MAX_BUY_TAX": float(os.getenv("MAX_BUY_TAX", 10)),
            "MAX_SELL_TAX": float(os.getenv("MAX_SELL_TAX", 15)),
            "MAX_TOTAL_TAX": float(os.getenv("MAX_TOTAL_TAX", 20)),
            
            # === SÉCURITÉ ===
            "CHECK_CONTRACT_VERIFIED": os.getenv("CHECK_CONTRACT_VERIFIED", "true").lower() == "true",
            "CHECK_OWNERSHIP_RENOUNCED": os.getenv("CHECK_OWNERSHIP_RENOUNCED", "true").lower() == "true",
            "CHECK_MINT_FUNCTION": os.getenv("CHECK_MINT_FUNCTION", "true").lower() == "true",
            "CHECK_BLACKLIST_FUNCTION": os.getenv("CHECK_BLACKLIST_FUNCTION", "true").lower() == "true",
            
            # === SLIPPAGE & GAS ===
            "MAX_SLIPPAGE_PERCENT": float(os.getenv("MAX_SLIPPAGE_PERCENT", 5)),
            "GAS_PRIORITY": os.getenv("GAS_PRIORITY", "MEDIUM"),
            "MAX_GAS_PRICE_GWEI": int(os.getenv("MAX_GAS_PRICE_GWEI", 100)),
            
            # === NOTIFICATIONS ===
            "ENABLE_TELEGRAM_ALERTS": os.getenv("ENABLE_TELEGRAM_ALERTS", "false").lower() == "true",
            "ENABLE_DISCORD_ALERTS": os.getenv("ENABLE_DISCORD_ALERTS", "false").lower() == "true",
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
            "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL", ""),
            
            # === WHALE TRACKING ===
            "ENABLE_WHALE_TRACKING": os.getenv("ENABLE_WHALE_TRACKING", "false").lower() == "true",
            "WHALE_MIN_HOLDINGS_USD": float(os.getenv("WHALE_MIN_HOLDINGS_USD", 100000)),
            
            # === STRATÉGIE ===
            "ACTIVE_STRATEGY": os.getenv("ACTIVE_STRATEGY", "CUSTOM"),
        }

app_state = AppState()

# ============================================================================
# RPC MANAGER
# ============================================================================

class RPCManager:
    def __init__(self):
        self.rpcs = {
            'ETH': os.getenv('ETH_RPC_URL'),
            'BSC': os.getenv('BSC_RPC_URL'),
            'BASE': os.getenv('BASE_RPC_URL'),
            'ARBITRUM': os.getenv('ARBITRUM_RPC_URL'),
            'POLYGON': os.getenv('POLYGON_RPC_URL'),
        }
        self.rpcs = {k: v for k, v in self.rpcs.items() if v}
    
    def get(self, chain: str) -> str:
        return self.rpcs.get(chain)

rpc_manager = RPCManager()

# ============================================================================
# SCANNER
# ============================================================================

async def start_scanning():
    """Démarre le scan avec le détecteur amélioré"""
    
    # Déterminer les chains actives
    enabled_chains = []
    if app_state.settings["ENABLE_ETH_DETECTION"] and rpc_manager.get("ETH"):
        enabled_chains.append("ETH")
    if app_state.settings["ENABLE_BSC_DETECTION"] and rpc_manager.get("BSC"):
        enabled_chains.append("BSC")
    if app_state.settings["ENABLE_BASE_DETECTION"] and rpc_manager.get("BASE"):
        enabled_chains.append("BASE")
    if app_state.settings["ENABLE_ARBITRUM_DETECTION"] and rpc_manager.get("ARBITRUM"):
        enabled_chains.append("ARBITRUM")
    
    if not enabled_chains:
        logger.warning("⚠️ Aucune blockchain activée pour le scan")
        return
    
    logger.info(f"🚀 Démarrage du scan sur: {', '.join(enabled_chains)}")
    
    # Créer le détecteur
    app_state.detector = MultiChainDetector(
        chains=enabled_chains,
        rpc_manager=rpc_manager,
        config=app_state.settings
    )
    
    # Task pour traiter les détections
    asyncio.create_task(process_detections())
    
    # Lancer le scan
    await app_state.detector.start()

async def process_detections():
    """Traite les détections et les envoie au dashboard"""
    while True:
        try:
            if app_state.detector and app_state.detector.event_queue:
                detection_dict = await app_state.detector.event_queue.get()
                
                # Convertir en TokenDetection
                detection = TokenDetection(
                    id=detection_dict.get('id', f"det_{datetime.utcnow().timestamp()}"),
                    symbol=detection_dict.get('symbol', 'UNK'),
                    name=detection_dict.get('name', 'Unknown'),
                    chain=detection_dict['chain'],
                    dex=detection_dict['dex'],
                    token_address=detection_dict['token_address'],
                    pair_address=detection_dict['pair_address'],
                    liquidity_usd=detection_dict.get('liquidity_usd', 0),
                    liquidity_native=detection_dict.get('liquidity_native', 0),
                    native_token=detection_dict.get('native_token', 'ETH'),
                    price_usd=detection_dict.get('price_usd', 0),
                    price_native=detection_dict.get('price_native', 0),
                    market_cap_usd=detection_dict.get('market_cap_usd', 0),
                    holders_count=detection_dict.get('holders_count', 0),
                    token_age_minutes=detection_dict.get('age_seconds', 0) // 60,
                    reliability_score=detection_dict.get('reliability_score', 50),
                    risk_score=detection_dict.get('risk_score', 50),
                    owner_address=detection_dict.get('owner_address', 'N/A'),
                    owner_balance_percent=detection_dict.get('owner_balance_percent', 0),
                    ownership_renounced=detection_dict.get('ownership_renounced', False),
                    has_mint_function=detection_dict.get('has_mint_function', False),
                    has_pause_function=detection_dict.get('has_pause_function', False),
                    has_blacklist=detection_dict.get('has_blacklist', False),
                    has_proxy=detection_dict.get('has_proxy', False),
                    links=detection_dict.get('links', {}),
                    timestamp=datetime.utcnow()
                )
                
                # Ajouter à la liste
                app_state.recent_detections.insert(0, detection)
                if len(app_state.recent_detections) > 100:
                    app_state.recent_detections.pop()
                
                # Mettre à jour stats
                app_state.stats["total_detections"] += 1
                app_state.stats["passed_filters"] += 1
                
                # Envoyer au dashboard via WebSocket
                await broadcast_websocket({
                    "type": "new_detection",
                    "data": detection.to_dict()
                })
                
                logger.info(f"✅ Token: {detection.symbol} ({detection.chain}) - Score: {detection.reliability_score} - Risk: {detection.risk_score}")
                
        except Exception as e:
            logger.error(f"Error processing detection: {e}")
            await asyncio.sleep(1)

# ============================================================================
# WEBSOCKET
# ============================================================================

async def broadcast_websocket(message: dict):
    """Broadcast à tous les clients WebSocket"""
    disconnected = []
    for ws in app_state.websocket_clients:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    for ws in disconnected:
        if ws in app_state.websocket_clients:
            app_state.websocket_clients.remove(ws)

async def broadcast_stats_loop():
    """Broadcast des stats toutes les 5 secondes"""
    while True:
        await asyncio.sleep(5)
        
        try:
            stats_data = {
                "type": "stats_update",
                "data": {
                    **app_state.stats,
                    "start_time": app_state.stats["start_time"].isoformat(),
                    "last_scan_time": app_state.stats["last_scan_time"].isoformat() if app_state.stats["last_scan_time"] else None,
                    "next_scan_time": app_state.stats["next_scan_time"].isoformat() if app_state.stats["next_scan_time"] else None,
                }
            }
            
            await broadcast_websocket(stats_data)
        except Exception as e:
            logger.error(f"Stats broadcast error: {e}")

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle"""
    logger.info("="*80)
    logger.info("🎯 RUG HUNTER BOT v5.0 - ULTIMATE EDITION WITH DIRECT LINKS")
    logger.info("="*80)
    logger.info(f"📊 Mode: {app_state.settings['TRADING_MODE']}")
    logger.info(f"🎯 Strategy: {app_state.settings['ACTIVE_STRATEGY']}")
    logger.info(f"🤖 Auto-Trading: {'✅ ENABLED' if app_state.settings['AUTO_TRADING_ENABLED'] else '❌ DISABLED'}")
    logger.info(f"⏱️  Scan Interval: {app_state.settings['SCAN_INTERVAL_SECONDS']}s")
    logger.info("="*80)
    
    # Démarrer tâches de fond
    if app_state.settings["SCAN_ENABLED"]:
        asyncio.create_task(start_scanning())
    asyncio.create_task(broadcast_stats_loop())
    
    yield
    
    logger.info("🛑 Shutting down...")
    if app_state.detector:
        await app_state.detector.stop()

app = FastAPI(
    title="RUG HUNTER API v5.0", 
    version="5.0.0", 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir le frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    try:
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    except:
        pass

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def serve_dashboard():
    """Sert le dashboard"""
    dashboard_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {"error": "Dashboard not found"}

@app.websocket("/ws/feed")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket feed"""
    await websocket.accept()
    app_state.websocket_clients.append(websocket)
    logger.info(f"📡 WebSocket connected ({len(app_state.websocket_clients)} clients)")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "data": {
                "mode": app_state.settings["TRADING_MODE"],
                "strategy": app_state.settings["ACTIVE_STRATEGY"],
                "auto_trading": app_state.settings["AUTO_TRADING_ENABLED"],
            }
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in app_state.websocket_clients:
            app_state.websocket_clients.remove(websocket)

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "5.0.0",
        "mode": app_state.settings["TRADING_MODE"],
        "scan_running": app_state.scan_running,
    }

@app.get("/api/stats")
async def get_stats():
    stats = {**app_state.stats}
    stats["start_time"] = stats["start_time"].isoformat()
    if stats["last_scan_time"]:
        stats["last_scan_time"] = stats["last_scan_time"].isoformat()
    if stats["next_scan_time"]:
        stats["next_scan_time"] = stats["next_scan_time"].isoformat()
    return stats

@app.get("/api/settings")
async def get_settings():
    return {"settings": app_state.settings}

@app.post("/api/settings")
async def update_settings(data: Dict[str, Any]):
    try:
        updated = []
        for key, value in data.items():
            if key in app_state.settings:
                app_state.settings[key] = value
                updated.append(key)
                logger.info(f"⚙️ Setting updated: {key} = {value}")
        
        await broadcast_websocket({
            "type": "settings_updated",
            "data": {"updated": updated}
        })
        
        return {"success": True, "updated": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/detections")
async def get_detections(limit: int = 50):
    detections = [d.to_dict() for d in app_state.recent_detections[:limit]]
    return {"total": len(app_state.recent_detections), "detections": detections}

@app.get("/api/positions")
async def get_positions():
    return {"positions": app_state.active_positions}

@app.post("/api/emergency/stop")
async def emergency_stop():
    logger.warning("🚨 EMERGENCY STOP")
    app_state.settings["AUTO_TRADING_ENABLED"] = False
    app_state.settings["SCAN_ENABLED"] = False
    
    await broadcast_websocket({
        "type": "emergency_stop",
        "data": {"timestamp": datetime.utcnow().isoformat()}
    })
    
    return {"success": True}

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", 8000))
    uvicorn.run(
        "main_improved:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )