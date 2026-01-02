"""FastAPI Backend - Complete with Settings API"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.detector import MultiChainDetector
from core.token_analyzer import TokenAnalyzer
from ml.scorer import MLScorer
from ml.advanced_scorer import AdvancedTradingScorer
from api.routes import router, add_detection
from config.settings import Settings

# Import conditionnel des notifications
try:
    from notifications.telegram_notifier import TelegramNotifier
    from notifications.discord_notifier import DiscordNotifier
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    TelegramNotifier = None
    DiscordNotifier = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RPCManager:
    def __init__(self, settings):
        self.rpcs = {
            "ETH": settings.ETH_RPC_URL,
            "BSC": settings.BSC_RPC_URL,
        }
    
    def get(self, chain: str):
        return self.rpcs.get(chain, "")

class AppState:
    def __init__(self):
        self.settings = None
        self.trading_mode = "PAPER"
        self.detector = None
        self.analyzer = None
        self.advanced_scorer = None
        self.telegram = None
        self.discord = None

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting RUG HUNTER BOT - Complete Trading System")
    
    app_state.settings = Settings()
    app_state.trading_mode = app_state.settings.TRADING_MODE
    app_state.rpc_manager = RPCManager(app_state.settings)
    
    # ML System
    app_state.ml_scorer = MLScorer()
    app_state.advanced_scorer = AdvancedTradingScorer(app_state.ml_scorer)
    
    # Notifications (optionnel)
    if NOTIFICATIONS_AVAILABLE:
        telegram_token = getattr(app_state.settings, "TELEGRAM_BOT_TOKEN", "")
        telegram_chat = getattr(app_state.settings, "TELEGRAM_CHAT_ID", "")
        discord_webhook = getattr(app_state.settings, "DISCORD_WEBHOOK_URL", "")
        
        app_state.telegram = TelegramNotifier(telegram_token, telegram_chat)
        app_state.discord = DiscordNotifier(discord_webhook)
    
    # Analyzer
    config = {
        "ETHERSCAN_API_KEY": getattr(app_state.settings, "ETHERSCAN_API_KEY", ""),
        "BSCSCAN_API_KEY": getattr(app_state.settings, "BSCSCAN_API_KEY", ""),
    }
    app_state.analyzer = TokenAnalyzer(app_state.rpc_manager, app_state.ml_scorer, config)
    
    # Detector
    enabled_chains = []
    if getattr(app_state.settings, "ENABLE_ETH_DETECTION", True):
        enabled_chains.append("ETH")
    if getattr(app_state.settings, "ENABLE_BSC_DETECTION", True):
        enabled_chains.append("BSC")
    
    detection_config = {
        "MIN_LIQUIDITY_USD": getattr(app_state.settings, "MIN_LIQUIDITY_USD", 5000),
        "MAX_TOKEN_AGE_MINUTES": getattr(app_state.settings, "MAX_TOKEN_AGE_MINUTES", 30),
        "SCAN_BLOCK_INTERVAL": getattr(app_state.settings, "SCAN_BLOCK_INTERVAL", 3),
    }
    
    app_state.detector = MultiChainDetector(enabled_chains, app_state.rpc_manager, detection_config)
    
    logger.info(f"✅ Bot started in {app_state.trading_mode} mode")
    logger.info(f"📡 Monitoring: {enabled_chains}")
    logger.info(f"🤖 Auto-trading: DISABLED (manual mode)")
    
    # Démarrer
    asyncio.create_task(app_state.detector.start())
    asyncio.create_task(process_detections())
    
    yield
    
    logger.info("🛑 Shutting down...")
    if app_state.detector:
        app_state.detector.running = False

app = FastAPI(title="RUG HUNTER API", version="3.0.0", lifespan=lifespan)

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
        return FileResponse(frontend_path / "dashboard.html")

active_websockets = []

@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"📡 WebSocket connected (total: {len(active_websockets)})")
    try:
        while True:
            await asyncio.sleep(1)
    except:
        pass
    finally:
        active_websockets.remove(websocket)

async def process_detections():
    """Traite les détections"""
    logger.info("🔄 Detection processor started")
    
    while True:
        try:
            detection = await app_state.detector.event_queue.get()
            
            add_detection(detection)
            
            # Broadcast WebSocket
            for ws in active_websockets:
                try:
                    await ws.send_json({"type": "new_detection", "data": detection})
                except:
                    pass
            
            # Analyse
            logger.info(f"🔍 Analyzing: {detection['symbol']}...")
            
            async with app_state.analyzer as analyzer:
                base_analysis = await analyzer.analyze(
                    detection["token_address"],
                    detection["chain"],
                    detection.get("pair_address")
                )
                
                advanced_analysis = app_state.advanced_scorer.analyze_and_recommend(
                    base_analysis['indicators'],
                    detection
                )
            
            # Afficher recommandations
            print_trading_recommendations(detection, advanced_analysis)
            
            # Notifications
            if NOTIFICATIONS_AVAILABLE and app_state.telegram:
                await app_state.telegram.send_detection_alert(detection, advanced_analysis)
            if NOTIFICATIONS_AVAILABLE and app_state.discord:
                await app_state.discord.send_detection_alert(detection, advanced_analysis)
            
            # Broadcast analyse
            complete_data = {
                "detection": detection,
                "advanced_analysis": advanced_analysis
            }
            
            for ws in active_websockets:
                try:
                    await ws.send_json({"type": "complete_analysis", "data": complete_data})
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            await asyncio.sleep(1)

def print_trading_recommendations(detection: dict, analysis: dict):
    """Affiche les recommandations"""
    recommendation = analysis['trading_recommendation']
    print(f"\n{'='*80}")
    print(f"💹 {detection['symbol']} - {recommendation['action']}")
    print(f"Score: {analysis['final_score']['overall_score']:.1f}/100")
    print(f"{'='*80}\n")

# ============= API ROUTES POUR L'INTERFACE WEB =============

from pydantic import BaseModel
from typing import Optional

ENV_FILE = Path(__file__).parent.parent / ".env"

class BotSettings(BaseModel):
    TRADING_MODE: str
    AUTO_TRADING_ENABLED: bool
    MIN_AUTO_TRADE_CONFIDENCE: int
    ENABLE_ETH_DETECTION: bool
    ENABLE_BSC_DETECTION: bool
    MIN_LIQUIDITY_USD: int
    SCAN_BLOCK_INTERVAL: int
    MAX_TOKEN_AGE_MINUTES: int
    MAX_POSITION_SIZE_USD: int
    MAX_DAILY_LOSS_PERCENT: int
    MAX_PORTFOLIO_EXPOSURE_PERCENT: int
    TELEGRAM_BOT_TOKEN: Optional[str] = ""
    TELEGRAM_CHAT_ID: Optional[str] = ""
    DISCORD_WEBHOOK_URL: Optional[str] = ""
    ETH_RPC_URL: str
    BSC_RPC_URL: str

@app.get("/api/settings")
async def get_settings():
    """Récupère les paramètres actuels"""
    return {
        "TRADING_MODE": app_state.settings.TRADING_MODE,
        "AUTO_TRADING_ENABLED": getattr(app_state.settings, "AUTO_TRADING_ENABLED", False),
        "MIN_AUTO_TRADE_CONFIDENCE": getattr(app_state.settings, "MIN_AUTO_TRADE_CONFIDENCE", 75),
        "ENABLE_ETH_DETECTION": getattr(app_state.settings, "ENABLE_ETH_DETECTION", True),
        "ENABLE_BSC_DETECTION": getattr(app_state.settings, "ENABLE_BSC_DETECTION", True),
        "MIN_LIQUIDITY_USD": getattr(app_state.settings, "MIN_LIQUIDITY_USD", 5000),
        "SCAN_BLOCK_INTERVAL": getattr(app_state.settings, "SCAN_BLOCK_INTERVAL", 3),
        "MAX_TOKEN_AGE_MINUTES": getattr(app_state.settings, "MAX_TOKEN_AGE_MINUTES", 30),
        "MAX_POSITION_SIZE_USD": getattr(app_state.settings, "MAX_POSITION_SIZE_USD", 500),
        "MAX_DAILY_LOSS_PERCENT": getattr(app_state.settings, "MAX_DAILY_LOSS_PERCENT", 15),
        "MAX_PORTFOLIO_EXPOSURE_PERCENT": getattr(app_state.settings, "MAX_PORTFOLIO_EXPOSURE_PERCENT", 20),
        "TELEGRAM_BOT_TOKEN": getattr(app_state.settings, "TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": getattr(app_state.settings, "TELEGRAM_CHAT_ID", ""),
        "DISCORD_WEBHOOK_URL": getattr(app_state.settings, "DISCORD_WEBHOOK_URL", ""),
        "ETH_RPC_URL": app_state.settings.ETH_RPC_URL,
        "BSC_RPC_URL": app_state.settings.BSC_RPC_URL,
    }

@app.post("/api/settings")
async def update_settings(settings: BotSettings):
    """Met à jour les paramètres"""
    try:
        env_content = {}
        if ENV_FILE.exists():
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key] = value
        
        env_content.update({
            "TRADING_MODE": settings.TRADING_MODE,
            "AUTO_TRADING_ENABLED": str(settings.AUTO_TRADING_ENABLED).lower(),
            "MIN_AUTO_TRADE_CONFIDENCE": str(settings.MIN_AUTO_TRADE_CONFIDENCE),
            "ENABLE_ETH_DETECTION": str(settings.ENABLE_ETH_DETECTION).lower(),
            "ENABLE_BSC_DETECTION": str(settings.ENABLE_BSC_DETECTION).lower(),
            "MIN_LIQUIDITY_USD": str(settings.MIN_LIQUIDITY_USD),
            "SCAN_BLOCK_INTERVAL": str(settings.SCAN_BLOCK_INTERVAL),
            "MAX_TOKEN_AGE_MINUTES": str(settings.MAX_TOKEN_AGE_MINUTES),
            "MAX_POSITION_SIZE_USD": str(settings.MAX_POSITION_SIZE_USD),
            "MAX_DAILY_LOSS_PERCENT": str(settings.MAX_DAILY_LOSS_PERCENT),
            "MAX_PORTFOLIO_EXPOSURE_PERCENT": str(settings.MAX_PORTFOLIO_EXPOSURE_PERCENT),
            "TELEGRAM_BOT_TOKEN": settings.TELEGRAM_BOT_TOKEN or "",
            "TELEGRAM_CHAT_ID": settings.TELEGRAM_CHAT_ID or "",
            "DISCORD_WEBHOOK_URL": settings.DISCORD_WEBHOOK_URL or "",
            "ETH_RPC_URL": settings.ETH_RPC_URL,
            "BSC_RPC_URL": settings.BSC_RPC_URL,
        })
        
        with open(ENV_FILE, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        return {
            "success": True,
            "message": "Paramètres sauvegardés. Redémarrez le bot pour appliquer.",
            "settings": settings.dict()
        }
        
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/stats/live")
async def get_live_stats():
    """Statistiques en temps réel"""
    return {
        "bot_running": app_state.detector.running if app_state.detector else False,
        "chains_monitored": app_state.detector.chains if app_state.detector else [],
        "total_detections": app_state.detector.total_detections if app_state.detector else 0,
        "current_blocks": app_state.detector.last_scanned_blocks if app_state.detector else {},
        "active_positions": 0,
        "total_pnl": 0.0,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
