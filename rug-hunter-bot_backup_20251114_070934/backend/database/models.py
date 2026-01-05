"""Database Models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DetectedToken(Base):
    __tablename__ = "detected_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    chain = Column(String(10), nullable=False)
    token_address = Column(String(42), nullable=False)
    pair_address = Column(String(42))
    dex = Column(String(20))
    name = Column(String(100))
    symbol = Column(String(20))
    decimals = Column(Integer)
    detected_at = Column(DateTime, default=datetime.utcnow)
    block_number = Column(Integer)
    initial_liquidity_usd = Column(Float)
    analyzed = Column(Boolean, default=False)
    rug_risk_score = Column(Integer)
    profit_potential = Column(Integer)
    recommendation = Column(String(20))
    analysis_data = Column(JSON)
