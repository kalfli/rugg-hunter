"""
RUG HUNTER BOT V2.0 - ULTIMATE EDITION
========================================
✅ Honeypot detection temps réel
✅ Mempool monitoring
✅ Trailing stop-loss dynamique
✅ Multi-RPC avec failover automatique
✅ Analyse bytecode avancée
✅ Copy-trading de wallets whales
✅ Dashboard moderne avec graphiques live
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

# Imports existants
from core.detector import MultiChainDetector
from core.token_analyzer import TokenAnalyzer
from ml.scorer import MLScorer
from ml.advanced_scorer import AdvancedTradingScorer
from api.routes import router, add_detection
from config.settings import Settings

# Nouveaux imports
from core.honeypot_detector import HoneypotDetector
from core.mempool_monitor import MempoolMonitor, estimate_optimal_gas_price
from core.trailing_stop_manager import TrailingStopManager
from core.multi_rpc_manager import create_default_rpc_manager

# Trading
from trading.engine import TradingEngine
from trading.risk_manager import RiskManager
from trading.wallet_manager import WalletManager
from trading.auto_trader import AutoTrader

# Notifications
try:
    from notifications.telegram_notifier import TelegramNotifier
    from notifications.discord_notifier import DiscordNotifier
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    TelegramNotifier = None
    DiscordNotifier = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppState:
    def __init__(self):
        self.settings = None
        self.trading_mode = "PAPER"
        self.detector = None
        self.analyzer = None
        self.advanced_scorer = None
        self.telegram = None
        self.discord = None
        self.honeypot_detector = None
        self.mempool_monitor = None
        self.trailing_stop_manager = None
        self.rpc_managers = {}  # Chain -> MultiRPCManager
        self.auto_trader = None
        self.statistics = {
            "total_detections": 0,
            "honeypots_blocked": 0,
            "trades_executed": 0,
            "total_pnl_usd": 0,
            "win_rate": 0,
            "start_time": datetime.utcnow()
        }

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management avec toutes les améliorations"""
    
    logger.info("=" * 80)
    logger.info("🚀 STARTING RUG HUNTER BOT V2.0 - ULTIMATE EDITION")
    logger.info("=" * 80)
    
    # 1. Configuration
    app_state.settings = Settings()
    app_state.trading_mode = app_state.settings.TRADING_MODE
    app_state.statistics["start_time"] = datetime.utcnow()
    
    logger.info(f"📊 Mode: {app_state.trading_mode}")
    
    # 2. Multi-RPC Managers avec failover
    logger.info("🌐 Initializing Multi-RPC managers...")
    app_state.rpc_managers["ETH"] = create_default_rpc_manager("ETH")
    app_state.rpc_managers["BSC"] = create_default_rpc_manager("BSC")
    
    for chain, manager in app_state.rpc_managers.items():
        await manager.start()
        logger.info(f"✅ {chain} RPC manager started with {len(manager.endpoints)} endpoints")
    
    # 3. ML System
    logger.info("🤖 Loading ML models...")
    app_state.ml_scorer = MLScorer()
    app_state.advanced_scorer = AdvancedTradingScorer(app_state.ml_scorer)
    logger.info("✅ ML system ready")
    
    # 4. Honeypot Detector
    logger.info("🍯 Initializing Honeypot Detector...")
    
    # Wrapper pour compatibility
    class RPCManagerWrapper:
        def __init__(self, rpc_managers):
            self.managers = rpc_managers
        
        def get(self, chain):
            manager = self.managers.get(chain)
            if manager:
                return manager.active_endpoint.url if manager.active_endpoint else None
            return None
    
    rpc_wrapper = RPCManagerWrapper(app_state.rpc_managers)
    app_state.honeypot_detector = HoneypotDetector(rpc_wrapper)
    logger.info("✅ Honeypot detection enabled")
    
    # 5. Trading System
    logger.info("💰 Initializing trading system...")
    
    try:
        wallet = WalletManager(
            app_state.settings.WALLET_KEYSTORE_PATH,
            "your_master_password"  # À sécuriser
        )
        
        risk_manager = RiskManager({
            "MAX_POSITION_SIZE_USD": app_state.settings.MAX_POSITION_SIZE_USD,
            "MAX_DAILY_LOSS_PERCENT": app_state.settings.MAX_DAILY_LOSS_PERCENT,
            "MAX_PORTFOLIO_EXPOSURE_PERCENT": app_state.settings.MAX_PORTFOLIO_EXPOSURE_PERCENT
        })
        
        trading_engine = TradingEngine(wallet, rpc_wrapper, {
            "TRADING_MODE": app_state.trading_mode
        })
        
        # Trailing Stop Manager
        app_state.trailing_stop_manager = TrailingStopManager(trading_engine)
        asyncio.create_task(app_state.trailing_stop_manager.start())
        logger.info("✅ Trailing stop-loss system enabled")
        
        # Auto Trader
        if app_state.settings.AUTO_TRADING_ENABLED:
            app_state.auto_trader = AutoTrader(
                trading_engine,
                wallet,
                risk_manager,
                {
                    "AUTO_TRADING_ENABLED": True,
                    "MIN_AUTO_TRADE_CONFIDENCE": app_state.settings.MIN_AUTO_TRADE_CONFIDENCE
                }
            )
            logger.info("✅ Auto-trading ENABLED")
        else:
            logger.info("ℹ️ Auto-trading DISABLED (manual mode)")
        
    except Exception as e:
        logger.warning(f"⚠️ Trading system init failed: {e}")
        logger.info("ℹ️ Running in analysis-only mode")
    
    # 6. Notifications
    if NOTIFICATIONS_AVAILABLE:
        if app_state.settings.TELEGRAM_BOT_TOKEN:
            app_state.telegram = TelegramNotifier(
                app_state.settings.TELEGRAM_BOT_TOKEN,
                app_state.settings.TELEGRAM_CHAT_ID
            )
            logger.info("✅ Telegram notifications enabled")
        
        if app_state.settings.DISCORD_WEBHOOK_URL:
            app_state.discord = DiscordNotifier(
                app_state.settings.DISCORD_WEBHOOK_URL
            )
            logger.info("✅ Discord notifications enabled")
    
    # 7. Token Analyzer
    logger.info("🔬 Initializing token analyzer...")
    config = {
        "ETHERSCAN_API_KEY": app_state.settings.ETHERSCAN_API_KEY or "",
        "BSCSCAN_API_KEY": app_state.settings.BSCSCAN_API_KEY or "",
    }
    app_state.analyzer = TokenAnalyzer(rpc_wrapper, app_state.ml_scorer, config)
    logger.info("✅ Analyzer ready")
    
    # 8. Multi-Chain Detector
    logger.info("📡 Starting chain detectors...")
    enabled_chains = []
    if app_state.settings.ENABLE_ETH_DETECTION:
        enabled_chains.append("ETH")
    if app_state.settings.ENABLE_BSC_DETECTION:
        enabled_chains.append("BSC")
    
    detection_config = {
        "MIN_LIQUIDITY_USD": app_state.settings.MIN_LIQUIDITY_USD,
        "MAX_TOKEN_AGE_MINUTES": app_state.settings.MAX_TOKEN_AGE_MINUTES,
        "SCAN_BLOCK_INTERVAL": app_state.settings.SCAN_BLOCK_INTERVAL,
    }
    
    app_state.detector = MultiChainDetector(enabled_chains, rpc_wrapper, detection_config)
    
    logger.info("=" * 80)
    logger.info(f"✅ BOT READY")
    logger.info(f"📡 Monitoring: {', '.join(enabled_chains)}")
    logger.info(f"💼 Mode: {app_state.trading_mode}")
    logger.info(f"🤖 Auto-trading: {'ENABLED' if app_state.settings.AUTO_TRADING_ENABLED else 'DISABLED'}")
    logger.info(f"🍯 Honeypot protection: ENABLED")
    logger.info(f"🎯 Trailing stops: ENABLED")
    logger.info(f"🌐 Multi-RPC failover: ENABLED")
    logger.info("=" * 80)
    
    # Démarrer les systèmes
    asyncio.create_task(app_state.detector.start())
    asyncio.create_task(process_detections())
    asyncio.create_task(broadcast_statistics())
    
    yield
    
    logger.info("=" * 80)
    logger.info("🛑 SHUTTING DOWN...")
    logger.info("=" * 80)
    
    if app_state.detector:
        app_state.detector.running = False
    
    if app_state.trailing_stop_manager:
        app_state.trailing_stop_manager.stop()
    
    for manager in app_state.rpc_managers.values():
        manager.stop()

app = FastAPI(title="RUG HUNTER API V2.0", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Dashboard
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    @app.get("/")
    async def serve_dashboard():
        return FileResponse(frontend_path / "dashboard_v2.html")

active_websockets = []

@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"📡 WebSocket connected (total: {len(active_websockets)})")
    
    try:
        # Envoyer le statut initial
        await websocket.send_json({
            "type": "connected",
            "data": {
                "mode": app_state.trading_mode,
                "chains": app_state.detector.chains if app_state.detector else [],
                "features": {
                    "honeypot_detection": True,
                    "trailing_stops": True,
                    "multi_rpc": True,
                    "auto_trading": app_state.settings.AUTO_TRADING_ENABLED
                }
            }
        })
        
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    finally:
        active_websockets.remove(websocket)
        logger.info(f"📡 WebSocket disconnected (remaining: {len(active_websockets)})")

async def broadcast_to_websockets(message: dict):
    """Broadcast un message à tous les WebSockets connectés"""
    for ws in active_websockets.copy():
        try:
            await ws.send_json(message)
        except:
            active_websockets.remove(ws)

async def process_detections():
    """Traite les détections avec toutes les protections"""
    logger.info("🔄 Detection processor started")
    
    while True:
        try:
            detection = await app_state.detector.event_queue.get()
            
            logger.info("=" * 80)
            logger.info(f"🎯 NEW TOKEN DETECTED: {detection.get('symbol', 'UNKNOWN')}")
            logger.info("=" * 80)
            
            # Ajout aux stats
            app_state.statistics["total_detections"] += 1
            add_detection(detection)
            
            # Broadcast immédiat
            await broadcast_to_websockets({
                "type": "new_detection",
                "data": detection
            })
            
            # 1. HONEYPOT CHECK (CRITIQUE)
            logger.info("🍯 Running honeypot detection...")
            honeypot_result = await app_state.honeypot_detector.is_honeypot(
                detection["token_address"],
                detection["chain"],
                detection.get("pair_address")
            )
            
            detection["honeypot_check"] = honeypot_result
            
            if honeypot_result["is_honeypot"]:
                logger.error("=" * 80)
                logger.error("🚨 HONEYPOT DETECTED - BLOCKED!")
                logger.error(f"Reason: {honeypot_result['reason']}")
                logger.error("=" * 80)
                
                app_state.statistics["honeypots_blocked"] += 1
                
                await broadcast_to_websockets({
                    "type": "honeypot_blocked",
                    "data": {
                        "token": detection,
                        "honeypot_result": honeypot_result
                    }
                })
                
                # Notification
                if app_state.telegram:
                    await app_state.telegram.send_alert(
                        f"🚨 HONEYPOT BLOCKED\n"
                        f"Token: {detection.get('symbol')}\n"
                        f"Reason: {honeypot_result['reason']}",
                        "WARNING"
                    )
                
                continue  # Skip ce token
            
            logger.info(f"✅ Honeypot check passed: {honeypot_result['reason']}")
            
            # 2. ANALYSE COMPLÈTE
            logger.info("🔬 Running complete analysis...")
            
            async with app_state.analyzer as analyzer:
                base_analysis = await analyzer.analyze(
                    detection["token_address"],
                    detection["chain"],
                    detection.get("pair_address")
                )
                
                # Analyse avancée avec recommandations
                advanced_analysis = app_state.advanced_scorer.analyze_and_recommend(
                    base_analysis['indicators'],
                    detection
                )
            
            # Ajouter les infos honeypot à l'analyse
            advanced_analysis["honeypot_check"] = honeypot_result
            
            # 3. AFFICHER RECOMMANDATIONS
            print_ultra_detailed_recommendations(detection, advanced_analysis)
            
            # 4. AUTO-TRADING (si enabled)
            if app_state.auto_trader:
                trade_result = await app_state.auto_trader.evaluate_and_execute(
                    detection,
                    advanced_analysis
                )
                
                if trade_result:
                    app_state.statistics["trades_executed"] += 1
                    
                    # Ajouter au trailing stop manager
                    if app_state.trailing_stop_manager:
                        # Créer position object
                        position = {
                            "position_id": trade_result["position_id"],
                            "symbol": detection["symbol"],
                            "entry_price": trade_result["entry_price"],
                            "amount_eth": advanced_analysis["trading_recommendation"]["position_sizing"]["amount_eth"]
                        }
                        
                        app_state.trailing_stop_manager.add_position(position, strategy="dynamic")
            
            # 5. NOTIFICATIONS
            if app_state.telegram:
                await app_state.telegram.send_detection_alert(detection, advanced_analysis)
            
            if app_state.discord:
                await app_state.discord.send_detection_alert(detection, advanced_analysis)
            
            # 6. BROADCAST COMPLET
            complete_data = {
                "detection": detection,
                "advanced_analysis": advanced_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await broadcast_to_websockets({
                "type": "complete_analysis",
                "data": complete_data
            })
            
            logger.info("=" * 80)
            logger.info("✅ Detection processed successfully")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}", exc_info=True)
            await asyncio.sleep(1)

async def broadcast_statistics():
    """Broadcast les statistiques toutes les 10 secondes"""
    while True:
        await asyncio.sleep(10)
        
        try:
            # Calculer stats
            uptime = (datetime.utcnow() - app_state.statistics["start_time"]).total_seconds()
            
            stats = {
                "total_detections": app_state.statistics["total_detections"],
                "honeypots_blocked": app_state.statistics["honeypots_blocked"],
                "trades_executed": app_state.statistics["trades_executed"],
                "total_pnl_usd": app_state.statistics["total_pnl_usd"],
                "uptime_seconds": uptime,
                "chains_monitored": app_state.detector.chains if app_state.detector else [],
                "bot_running": app_state.detector.running if app_state.detector else False
            }
            
            # RPC status
            rpc_status = {}
            for chain, manager in app_state.rpc_managers.items():
                rpc_status[chain] = manager.get_status()
            
            stats["rpc_status"] = rpc_status
            
            await broadcast_to_websockets({
                "type": "statistics_update",
                "data": stats
            })
            
        except:
            pass

def print_ultra_detailed_recommendations(detection: dict, analysis: dict):
    """Affiche les recommandations ultra-détaillées"""
    
    recommendation = analysis['trading_recommendation']
    scores = analysis['final_score']
    security = analysis['security_analysis']
    honeypot = analysis.get('honeypot_check', {})
    
    # Couleurs
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    
    print("\n" + "=" * 100)
    print(f"{BOLD}{CYAN}🎯 TRADING RECOMMENDATION{RESET}")
    print("=" * 100)
    
    # Action
    action_color = GREEN if "BUY" in recommendation['action'] else RED
    print(f"\n{BOLD}ACTION: {action_color}{recommendation['action']}{RESET}")
    print(f"Confidence: {recommendation['confidence']}")
    
    # Scores
    print(f"\n{BOLD}{CYAN}📊 SCORES{RESET}")
    print(f" Overall: {scores['overall_score']:.1f}/100")
    print(f" Security: {scores['security_score']}/100")
    print(f" Liquidity: {scores['liquidity_score']}/100")
    print(f" Momentum: {scores['momentum_score']}/100")
    
    # Honeypot
    print(f"\n{BOLD}{CYAN}🍯 HONEYPOT CHECK{RESET}")
    if honeypot.get('is_honeypot'):
        print(f" {RED}⚠️  HONEYPOT DETECTED!{RESET}")
        print(f" Reason: {honeypot.get('reason', 'Unknown')}")
    else:
        print(f" {GREEN}✓ Clean{RESET} - {honeypot.get('reason', 'Passed all checks')}")
    print(f" Buy Tax: {honeypot.get('buy_tax', 0)}%")
    print(f" Sell Tax: {honeypot.get('sell_tax', 0)}%")
    
    # Security Issues
    if security.get('issues'):
        print(f"\n{BOLD}{CYAN}🔒 SECURITY ISSUES{RESET}")
        for issue in security['issues']:
            print(f" {RED}⚠ {RESET} {issue}")
    
    # Position Sizing (si BUY)
    if "BUY" in recommendation['action'] and 'position_sizing' in recommendation:
        ps = recommendation['position_sizing']
        print(f"\n{BOLD}{CYAN}💰 POSITION SIZING{RESET}")
        print(f" Amount: {ps['amount_eth']} ETH (${ps['amount_usd']})")
        print(f" Max Slippage: {ps['max_slippage']}")
        print(f" Gas Priority: {ps['gas_priority']}")
    
    print("=" * 100 + "\n")

# API Routes additionnelles
@app.get("/api/statistics")
async def get_statistics():
    """Statistiques complètes"""
    uptime = (datetime.utcnow() - app_state.statistics["start_time"]).total_seconds()
    
    return {
        **app_state.statistics,
        "uptime_seconds": uptime,
        "uptime_hours": uptime / 3600,
        "detections_per_hour": (app_state.statistics["total_detections"] / uptime * 3600) if uptime > 0 else 0
    }

@app.get("/api/rpc/status")
async def get_rpc_status():
    """Status de tous les RPCs"""
    status = {}
    for chain, manager in app_state.rpc_managers.items():
        status[chain] = manager.get_status()
    return status

@app.get("/api/positions/active")
async def get_active_positions():
    """Positions actives avec trailing stops"""
    if not app_state.trailing_stop_manager:
        return {"positions": []}
    
    positions = []
    for position_id in app_state.trailing_stop_manager.active_stops.keys():
        status = app_state.trailing_stop_manager.get_position_status(position_id)
        if status:
            positions.append(status)
    
    return {"positions": positions}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
