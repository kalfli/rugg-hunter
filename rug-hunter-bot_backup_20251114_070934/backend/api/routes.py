"""API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()

# Stockage en mémoire des dernières détections
recent_detections = []
MAX_DETECTIONS = 50

class AnalyzeRequest(BaseModel):
    address: str
    chain: str
    pair_address: Optional[str] = None

@router.get("/api/health")
async def health():
    from main import app_state
    return {
        "status": "ok",
        "mode": app_state.trading_mode,
        "chains_monitored": app_state.detector.chains if app_state.detector else [],
        "detector_running": app_state.detector.running if app_state.detector else False,
        "total_detected": len(recent_detections),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/api/analyze/token")
async def analyze_token(request: AnalyzeRequest):
    from main import app_state
    
    if not app_state.analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    async with app_state.analyzer as analyzer:
        result = await analyzer.analyze(request.address, request.chain, request.pair_address)
    
    return result

@router.get("/api/detections/recent")
async def get_recent_detections(limit: int = 20):
    """Récupère les dernières détections"""
    return {
        "total": len(recent_detections),
        "detections": recent_detections[-limit:][::-1] # Les plus récentes en premier
    }

@router.get("/api/detections/latest")
async def get_latest_detection():
    """Récupère la toute dernière détection"""
    if not recent_detections:
        return {"message": "No detections yet"}
    return recent_detections[-1]

@router.get("/api/positions/active")
async def get_active_positions():
    return {"positions": []}

@router.post("/api/emergency/stop")
async def emergency_stop():
    from main import app_state
    if app_state.detector:
        app_state.detector.running = False
    return {"stopped": True}

def add_detection(detection: dict):
    """Ajoute une détection à l'historique"""
    recent_detections.append(detection)
    if len(recent_detections) > MAX_DETECTIONS:
        recent_detections.pop(0)
