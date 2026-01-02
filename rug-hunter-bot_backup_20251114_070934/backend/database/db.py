"""Database Manager"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
    
    def init_db(self):
        """Initialise la base de données"""
        try:
            self.engine = create_engine(self.database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized")
        except Exception as e:
            logger.warning(f"Database init failed: {e}")
            self.engine = None
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager pour session DB"""
        if not self.SessionLocal:
            yield None
            return
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    async def save_detection(self, detection_data: dict):
        """Sauvegarde une détection"""
        if not self.engine:
            return
        
        try:
            from .models import DetectedToken
            with self.get_session() as session:
                if session:
                    token = DetectedToken(
                        chain=detection_data["chain"],
                        token_address=detection_data["token_address"],
                        pair_address=detection_data.get("pair_address"),
                        dex=detection_data.get("dex"),
                        name=detection_data.get("name"),
                        symbol=detection_data.get("symbol"),
                        initial_liquidity_usd=detection_data.get("liquidity_usd"),
                        block_number=detection_data.get("block_number")
                    )
                    session.add(token)
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
    
    async def save_analysis(self, token_address: str, chain: str, analysis: dict):
        """Sauvegarde une analyse"""
        if not self.engine:
            return
        
        try:
            from .models import DetectedToken
            with self.get_session() as session:
                if session:
                    token = session.query(DetectedToken).filter_by(
                        token_address=token_address,
                        chain=chain
                    ).first()
                    
                    if token:
                        token.analyzed = True
                        token.rug_risk_score = analysis["rug_risk_score"]
                        token.profit_potential = analysis["profit_potential"]
                        token.recommendation = analysis["recommendation"]
                        token.analysis_data = analysis
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
