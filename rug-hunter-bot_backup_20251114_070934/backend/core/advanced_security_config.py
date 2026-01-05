"""
🛡️ RUG HUNTER BOT V3.0 - Système de Sécurité Avancé
Gestion complète de la sécurité et de la détection des risques
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Niveaux de risque"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityConfig:
    """Configuration de sécurité complète"""
    
    # ========================================================================
    # HONEYPOT DETECTION
    # ========================================================================
    
    # Taxes maximales acceptables
    max_buy_tax: float = 10.0  # %
    max_sell_tax: float = 15.0  # %
    max_transfer_tax: float = 5.0  # %
    
    # Autorités
    block_freeze_authority: bool = True
    block_mint_authority: bool = True
    require_ownership_renounced: bool = False  # Optionnel mais recommandé
    
    # Liquidité
    min_liquidity_locked_percent: float = 50.0  # %
    min_liquidity_lock_days: int = 30  # jours
    
    # Vérification
    require_verified_contract: bool = True
    require_audit: bool = False  # Optionnel
    
    # ========================================================================
    # RISK MANAGEMENT
    # ========================================================================
    
    # Limites de position
    max_position_size_usd: float = 500.0
    max_position_size_percent_portfolio: float = 20.0
    max_concurrent_positions: int = 5
    
    # Limites de perte
    max_loss_per_trade_percent: float = 5.0
    max_daily_loss_usd: float = 500.0
    max_daily_loss_percent: float = 15.0
    max_weekly_loss_percent: float = 30.0
    
    # Stop loss / Take profit
    default_stop_loss_percent: float = 5.0
    default_take_profit_percent: float = 20.0
    use_trailing_stop: bool = True
    trailing_stop_activation_percent: float = 10.0  # Active après +10%
    trailing_stop_distance_percent: float = 5.0
    
    # ========================================================================
    # AUTO-TRADING
    # ========================================================================
    
    auto_trading_enabled: bool = False
    min_confidence_score: float = 75.0
    max_trades_per_hour: int = 5
    max_trades_per_day: int = 20
    
    # Cool-down après perte
    cooldown_after_loss_minutes: int = 30
    cooldown_after_3_losses: int = 120  # 2 heures
    
    # ========================================================================
    # DETECTION FILTERS
    # ========================================================================
    
    # Liquidité
    min_liquidity_usd: float = 5000.0
    min_liquidity_ratio: float = 1.0  # Ratio liquidité/market cap
    
    # Âge du token
    min_token_age_minutes: int = 5
    max_token_age_minutes: int = 30
    
    # Holders
    min_holders: int = 50
    max_top_holder_percent: float = 20.0
    max_top10_holders_percent: float = 50.0
    
    # Volume
    min_volume_24h_usd: float = 1000.0
    min_volume_to_liquidity_ratio: float = 0.1
    
    # Prix
    max_price_volatility_1h: float = 50.0  # %
    max_price_impact: float = 10.0  # % pour trade de taille moyenne
    
    # ========================================================================
    # CHAIN SPECIFIC
    # ========================================================================
    
    # ETH / BSC
    eth_min_gas_for_buy: int = 100000
    eth_min_gas_for_sell: int = 100000
    eth_max_gas_price_gwei: float = 100.0
    
    # Solana
    sol_require_no_freeze_authority: bool = True
    sol_require_no_mint_authority: bool = True
    sol_min_account_age_seconds: int = 300  # 5 minutes


class AdvancedSecurityChecker:
    """
    Vérificateur de sécurité avancé avec scores détaillés
    """
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def check_token_security(self, token_data: Dict) -> Dict:
        """
        Effectue un check de sécurité complet
        Retourne un dictionnaire avec score et détails
        """
        result = {
            "is_safe": True,
            "risk_level": RiskLevel.VERY_LOW,
            "risk_score": 0,  # 0-100 (0 = très sûr, 100 = très dangereux)
            "checks": {},
            "warnings": [],
            "blockers": []
        }
        
        # 1. Honeypot checks
        honeypot_score = self._check_honeypot(token_data, result)
        
        # 2. Liquidity checks
        liquidity_score = self._check_liquidity(token_data, result)
        
        # 3. Holders checks
        holders_score = self._check_holders(token_data, result)
        
        # 4. Contract checks
        contract_score = self._check_contract(token_data, result)
        
        # 5. Trading checks
        trading_score = self._check_trading(token_data, result)
        
        # 6. Age checks
        age_score = self._check_age(token_data, result)
        
        # Calculer score final
        weights = {
            "honeypot": 0.3,
            "liquidity": 0.2,
            "holders": 0.15,
            "contract": 0.15,
            "trading": 0.1,
            "age": 0.1
        }
        
        result["risk_score"] = (
            honeypot_score * weights["honeypot"] +
            liquidity_score * weights["liquidity"] +
            holders_score * weights["holders"] +
            contract_score * weights["contract"] +
            trading_score * weights["trading"] +
            age_score * weights["age"]
        )
        
        # Déterminer le niveau de risque
        if result["risk_score"] >= 80:
            result["risk_level"] = RiskLevel.CRITICAL
            result["is_safe"] = False
        elif result["risk_score"] >= 60:
            result["risk_level"] = RiskLevel.HIGH
            result["is_safe"] = False
        elif result["risk_score"] >= 40:
            result["risk_level"] = RiskLevel.MEDIUM
        elif result["risk_score"] >= 20:
            result["risk_level"] = RiskLevel.LOW
        else:
            result["risk_level"] = RiskLevel.VERY_LOW
        
        # Ajouter recommendation
        result["recommendation"] = self._get_recommendation(result)
        
        return result
    
    def _check_honeypot(self, token_data: Dict, result: Dict) -> float:
        """Vérifie les indicateurs de honeypot"""
        score = 0
        honeypot = token_data.get("honeypot_check", {})
        
        # Buy tax
        buy_tax = honeypot.get("buy_tax", 0)
        if buy_tax > self.config.max_buy_tax:
            score += 30
            result["blockers"].append(f"Buy tax trop élevée: {buy_tax}%")
        elif buy_tax > self.config.max_buy_tax * 0.7:
            score += 15
            result["warnings"].append(f"Buy tax élevée: {buy_tax}%")
        
        # Sell tax
        sell_tax = honeypot.get("sell_tax", 0)
        if sell_tax > self.config.max_sell_tax:
            score += 30
            result["blockers"].append(f"Sell tax trop élevée: {sell_tax}%")
        elif sell_tax > self.config.max_sell_tax * 0.7:
            score += 15
            result["warnings"].append(f"Sell tax élevée: {sell_tax}%")
        
        # Can sell?
        if not honeypot.get("can_sell", True):
            score += 50
            result["blockers"].append("Impossible de vendre - HONEYPOT confirmé!")
        
        # Freeze authority (Solana)
        if token_data.get("chain") == "SOL":
            if token_data.get("freeze_authority") and self.config.sol_require_no_freeze_authority:
                score += 25
                result["warnings"].append("Freeze authority présente")
        
        result["checks"]["honeypot"] = {
            "score": score,
            "buy_tax": buy_tax,
            "sell_tax": sell_tax,
            "can_sell": honeypot.get("can_sell", True)
        }
        
        return score
    
    def _check_liquidity(self, token_data: Dict, result: Dict) -> float:
        """Vérifie la liquidité"""
        score = 0
        liquidity_usd = token_data.get("liquidity_usd", 0)
        
        if liquidity_usd < self.config.min_liquidity_usd:
            score += 40
            result["blockers"].append(f"Liquidité trop faible: ${liquidity_usd:,.0f}")
        elif liquidity_usd < self.config.min_liquidity_usd * 2:
            score += 20
            result["warnings"].append(f"Liquidité faible: ${liquidity_usd:,.0f}")
        
        # Liquidity ratio
        market_cap = token_data.get("market_cap_usd", 0)
        if market_cap > 0:
            liq_ratio = liquidity_usd / market_cap
            if liq_ratio < self.config.min_liquidity_ratio:
                score += 15
                result["warnings"].append(f"Ratio liquidité/MC faible: {liq_ratio:.2f}")
        
        result["checks"]["liquidity"] = {
            "score": score,
            "liquidity_usd": liquidity_usd,
            "min_required": self.config.min_liquidity_usd
        }
        
        return score
    
    def _check_holders(self, token_data: Dict, result: Dict) -> float:
        """Vérifie la distribution des holders"""
        score = 0
        holders = token_data.get("holders", 0)
        
        if holders < self.config.min_holders:
            score += 25
            result["warnings"].append(f"Peu de holders: {holders}")
        
        # Top holders concentration
        top10_percent = token_data.get("top10_holders_percent", 100)
        if top10_percent > self.config.max_top10_holders_percent:
            score += 20
            result["warnings"].append(f"Top 10 holders: {top10_percent:.1f}%")
        
        result["checks"]["holders"] = {
            "score": score,
            "count": holders,
            "top10_percent": top10_percent
        }
        
        return score
    
    def _check_contract(self, token_data: Dict, result: Dict) -> float:
        """Vérifie le contrat"""
        score = 0
        
        # Contract verified?
        if self.config.require_verified_contract:
            if not token_data.get("contract_verified", False):
                score += 30
                result["blockers"].append("Contrat non vérifié")
        
        # Ownership renounced?
        if self.config.require_ownership_renounced:
            if not token_data.get("ownership_renounced", False):
                score += 15
                result["warnings"].append("Ownership non renoncé")
        
        # Audit?
        if self.config.require_audit:
            if not token_data.get("audited", False):
                score += 20
                result["warnings"].append("Pas d'audit")
        
        result["checks"]["contract"] = {
            "score": score,
            "verified": token_data.get("contract_verified", False),
            "renounced": token_data.get("ownership_renounced", False),
            "audited": token_data.get("audited", False)
        }
        
        return score
    
    def _check_trading(self, token_data: Dict, result: Dict) -> float:
        """Vérifie l'activité de trading"""
        score = 0
        
        # Volume
        volume_24h = token_data.get("volume_24h_usd", 0)
        if volume_24h < self.config.min_volume_24h_usd:
            score += 15
            result["warnings"].append(f"Volume faible: ${volume_24h:,.0f}")
        
        # Volatility
        price_change = abs(token_data.get("price_change_1h", 0))
        if price_change > self.config.max_price_volatility_1h:
            score += 20
            result["warnings"].append(f"Volatilité élevée: {price_change:.1f}%")
        
        result["checks"]["trading"] = {
            "score": score,
            "volume_24h": volume_24h,
            "volatility": price_change
        }
        
        return score
    
    def _check_age(self, token_data: Dict, result: Dict) -> float:
        """Vérifie l'âge du token"""
        score = 0
        age_minutes = token_data.get("age_minutes", 0)
        
        if age_minutes < self.config.min_token_age_minutes:
            score += 25
            result["warnings"].append(f"Token très récent: {age_minutes}min")
        elif age_minutes > self.config.max_token_age_minutes:
            score += 10
            result["warnings"].append(f"Token trop vieux: {age_minutes}min")
        
        result["checks"]["age"] = {
            "score": score,
            "age_minutes": age_minutes
        }
        
        return score
    
    def _get_recommendation(self, result: Dict) -> str:
        """Génère une recommendation basée sur le résultat"""
        if result["risk_level"] == RiskLevel.CRITICAL:
            return "🚫 NE PAS TRADER - Risque critique"
        elif result["risk_level"] == RiskLevel.HIGH:
            return "⛔ Déconseillé - Risque élevé"
        elif result["risk_level"] == RiskLevel.MEDIUM:
            return "⚠️ Prudence - Risque modéré, trade manuel uniquement"
        elif result["risk_level"] == RiskLevel.LOW:
            return "✅ Acceptable - Peut être tradé avec précaution"
        else:
            return "🌟 Excellent - Bon candidat pour auto-trading"


class RiskManager:
    """
    Gestionnaire de risque en temps réel
    """
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.trades_today = 0
        self.trades_this_hour = 0
        self.active_positions = []
        self.last_loss_time = None
        self.consecutive_losses = 0
    
    def can_open_position(self, position_size_usd: float) -> Tuple[bool, str]:
        """Vérifie si une position peut être ouverte"""
        
        # Check position size
        if position_size_usd > self.config.max_position_size_usd:
            return False, f"Position trop grande (max: ${self.config.max_position_size_usd})"
        
        # Check concurrent positions
        if len(self.active_positions) >= self.config.max_concurrent_positions:
            return False, f"Trop de positions actives (max: {self.config.max_concurrent_positions})"
        
        # Check daily loss limit
        if self.daily_loss >= self.config.max_daily_loss_usd:
            return False, f"Limite de perte journalière atteinte (${self.daily_loss:.2f})"
        
        # Check trade limits
        if self.trades_this_hour >= self.config.max_trades_per_hour:
            return False, f"Limite horaire atteinte ({self.config.max_trades_per_hour} trades/h)"
        
        if self.trades_today >= self.config.max_trades_per_day:
            return False, f"Limite journalière atteinte ({self.config.max_trades_per_day} trades/j)"
        
        # Check cooldown
        if self.consecutive_losses >= 3:
            cooldown = self.config.cooldown_after_3_losses
            # TODO: Vérifier le temps écoulé depuis last_loss_time
            return False, f"Cool-down actif après 3 pertes consécutives ({cooldown}min)"
        
        return True, "OK"
    
    def record_trade(self, pnl_usd: float):
        """Enregistre un trade et met à jour les statistiques"""
        self.trades_today += 1
        self.trades_this_hour += 1
        
        if pnl_usd < 0:
            self.daily_loss += abs(pnl_usd)
            self.weekly_loss += abs(pnl_usd)
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def reset_daily(self):
        """Reset les compteurs journaliers"""
        self.daily_loss = 0.0
        self.trades_today = 0
    
    def reset_weekly(self):
        """Reset les compteurs hebdomadaires"""
        self.weekly_loss = 0.0


# ============================================================================
# PRESETS DE CONFIGURATION
# ============================================================================

SECURITY_PRESETS = {
    "CONSERVATIVE": SecurityConfig(
        max_buy_tax=5.0,
        max_sell_tax=10.0,
        require_verified_contract=True,
        require_ownership_renounced=True,
        min_liquidity_usd=20000,
        min_holders=100,
        max_position_size_usd=300,
        max_daily_loss_percent=10,
        min_confidence_score=85,
        max_trades_per_hour=3
    ),
    
    "MODERATE": SecurityConfig(
        max_buy_tax=10.0,
        max_sell_tax=15.0,
        require_verified_contract=True,
        require_ownership_renounced=False,
        min_liquidity_usd=10000,
        min_holders=50,
        max_position_size_usd=500,
        max_daily_loss_percent=15,
        min_confidence_score=75,
        max_trades_per_hour=5
    ),
    
    "AGGRESSIVE": SecurityConfig(
        max_buy_tax=15.0,
        max_sell_tax=20.0,
        require_verified_contract=False,
        require_ownership_renounced=False,
        min_liquidity_usd=5000,
        min_holders=20,
        max_position_size_usd=1000,
        max_daily_loss_percent=20,
        min_confidence_score=65,
        max_trades_per_hour=10
    )
}


def get_security_config(preset: str = "MODERATE") -> SecurityConfig:
    """Retourne une configuration de sécurité par preset"""
    return SECURITY_PRESETS.get(preset, SECURITY_PRESETS["MODERATE"])
