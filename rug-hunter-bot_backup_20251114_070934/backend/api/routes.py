"""API Routes - Version améliorée avec tous les liens"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

router = APIRouter()

# Stockage en mémoire
recent_detections = []
MAX_DETECTIONS = 100  # Augmenté à 100

class AnalyzeRequest(BaseModel):
    address: str
    chain: str
    pair_address: Optional[str] = None

class TradeRequest(BaseModel):
    action: str
    token_address: str
    amount_eth: float
    slippage: float
    wallet_address: Optional[str] = None
    chain: str = "ETH"

@router.get("/api/detections/recent")
async def get_recent_detections(limit: int = 20):
    """Récupère les dernières détections"""
    return {
        "total": len(recent_detections),
        "detections": recent_detections[-limit:][::-1]
    }

@router.get("/api/detections/latest")
async def get_latest_detection():
    """Récupère la toute dernière détection"""
    if not recent_detections:
        return {"message": "No detections yet"}
    return recent_detections[-1]

@router.get("/api/detections/all")
async def get_all_detections():
    """Récupère toutes les détections"""
    return {
        "total": len(recent_detections),
        "detections": recent_detections[::-1]  # Plus récent en premier
    }

@router.get("/api/detections/{chain}")
async def get_detections_by_chain(chain: str, limit: int = 20):
    """Récupère les détections pour une blockchain spécifique"""
    chain_detections = [d for d in recent_detections if d.get('chain', '').upper() == chain.upper()]
    return {
        "chain": chain,
        "total": len(chain_detections),
        "detections": chain_detections[-limit:][::-1]
    }

@router.get("/api/detection/{token_address}")
async def get_detection_by_address(token_address: str):
    """Récupère une détection spécifique par adresse de token"""
    for detection in reversed(recent_detections):
        if detection.get('token_address', '').lower() == token_address.lower():
            return detection
    raise HTTPException(status_code=404, detail="Token not found")

@router.get("/api/stats")
async def get_stats():
    """Statistiques générales"""
    if not recent_detections:
        return {
            "total_detections": 0,
            "chains": {},
            "recent_24h": 0
        }
    
    # Stats par chain
    chains_stats = {}
    for detection in recent_detections:
        chain = detection.get('chain', 'Unknown')
        if chain not in chains_stats:
            chains_stats[chain] = {
                "count": 0,
                "total_liquidity_usd": 0,
                "avg_liquidity_usd": 0
            }
        chains_stats[chain]["count"] += 1
        chains_stats[chain]["total_liquidity_usd"] += detection.get('liquidity_usd', 0)
    
    # Calcul des moyennes
    for chain in chains_stats:
        if chains_stats[chain]["count"] > 0:
            chains_stats[chain]["avg_liquidity_usd"] = (
                chains_stats[chain]["total_liquidity_usd"] / chains_stats[chain]["count"]
            )
    
    return {
        "total_detections": len(recent_detections),
        "chains": chains_stats,
        "recent_24h": len(recent_detections),  # Simplification
        "last_detection": recent_detections[-1] if recent_detections else None
    }

def add_detection(detection: dict):
    """Ajoute une détection à l'historique"""
    # Enrichir avec timestamp si absent
    if 'timestamp' not in detection:
        detection['timestamp'] = datetime.utcnow().isoformat()
    
    # Ajouter ID unique
    detection['id'] = len(recent_detections) + 1
    
    recent_detections.append(detection)
    
    # Limiter la taille
    if len(recent_detections) > MAX_DETECTIONS:
        recent_detections.pop(0)
    
    return detection