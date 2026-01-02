"""API Routes for Settings Management"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from pathlib import Path

router = APIRouter()

ENV_FILE = Path(__file__).parent.parent.parent / ".env"

class BotSettings(BaseModel):
    # Trading
    TRADING_MODE: str
    AUTO_TRADING_ENABLED: bool
    MIN_AUTO_TRADE_CONFIDENCE: int
    
    # Detection
    ENABLE_ETH_DETECTION: bool
    ENABLE_BSC_DETECTION: bool
    MIN_LIQUIDITY_USD: int
    SCAN_BLOCK_INTERVAL: int
    MAX_TOKEN_AGE_MINUTES: int
    
    # Risk Management
    MAX_POSITION_SIZE_USD: int
    MAX_DAILY_LOSS_PERCENT: int
    MAX_PORTFOLIO_EXPOSURE_PERCENT: int
    
    # Notifications
    TELEGRAM_BOT_TOKEN: Optional[str] = ""
    TELEGRAM_CHAT_ID: Optional[str] = ""
    DISCORD_WEBHOOK_URL: Optional[str] = ""
    
    # RPC
    ETH_RPC_URL: str
    BSC_RPC_URL: str

@router.get("/api/settings")
async def get_settings():
    """Récupère les paramètres actuels"""
    from main import app_state
    
    settings = {
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
    
    return settings

@router.post("/api/settings")
async def update_settings(settings: BotSettings):
    """Met à jour les paramètres"""
    try:
        # Lire le fichier .env actuel
        env_content = {}
        if ENV_FILE.exists():
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key] = value
        
        # Mettre à jour avec les nouvelles valeurs
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
        
        # Écrire le nouveau fichier .env
        with open(ENV_FILE, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        return {
            "success": True,
            "message": "Paramètres sauvegardés. Redémarrez le bot pour appliquer les changements.",
            "settings": settings.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/bot/restart")
async def restart_bot():
    """Redémarre le bot (nécessite supervisor ou systemd)"""
    return {
        "success": False,
        "message": "Redémarrage manuel requis. Utilisez: sudo systemctl restart rug-hunter"
    }

@router.get("/api/stats/live")
async def get_live_stats():
    """Statistiques en temps réel"""
    from main import app_state
    
    return {
        "bot_running": app_state.detector.running if app_state.detector else False,
        "chains_monitored": app_state.detector.chains if app_state.detector else [],
        "total_detections": app_state.detector.total_detections if app_state.detector else 0,
        "current_blocks": app_state.detector.last_scanned_blocks if app_state.detector else {},
        "active_positions": 0, # À implémenter
        "total_pnl": 0.0,
    }
