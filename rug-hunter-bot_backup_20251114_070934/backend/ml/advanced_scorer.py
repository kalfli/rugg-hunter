"""Advanced ML Scorer with Trading Recommendations"""
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedTradingScorer:
    def __init__(self, base_scorer):
        self.base_scorer = base_scorer
        
    def analyze_and_recommend(self, indicators: dict, detection_data: dict) -> dict:
        """Analyse complète avec recommandations de trading précises"""
        
        # Scores ML de base
        base_scores = self.base_scorer.predict(indicators)
        
        # Analyse approfondie
        security_analysis = self._analyze_security(indicators)
        liquidity_analysis = self._analyze_liquidity(indicators, detection_data)
        momentum_analysis = self._analyze_momentum(indicators)
        risk_analysis = self._calculate_risk_metrics(indicators, detection_data)
        
        # Calcul du score global
        final_score = self._calculate_final_score(
            base_scores,
            security_analysis,
            liquidity_analysis,
            momentum_analysis,
            risk_analysis
        )
        
        # Génération de recommandations
        trading_recommendation = self._generate_trading_recommendation(
            final_score,
            security_analysis,
            liquidity_analysis,
            momentum_analysis,
            risk_analysis,
            detection_data
        )
        
        return {
            "base_scores": base_scores,
            "security_analysis": security_analysis,
            "liquidity_analysis": liquidity_analysis,
            "momentum_analysis": momentum_analysis,
            "risk_analysis": risk_analysis,
            "final_score": final_score,
            "trading_recommendation": trading_recommendation
        }
    
    def _analyze_security(self, ind: dict) -> dict:
        """Analyse de sécurité détaillée"""
        security_score = 100
        issues = []
        warnings = []
        
        # Ownership
        if not ind.get('ownership_renounced', False):
            security_score -= 20
            issues.append("Owner not renounced - Can modify contract")
        
        # Dangerous functions
        if ind.get('has_mint_function', False):
            security_score -= 15
            issues.append("Mint function present - Supply can be inflated")
        
        if ind.get('has_pause_function', False):
            security_score -= 10
            warnings.append("Pause function present - Trading can be stopped")
        
        if ind.get('has_blacklist_function', False):
            security_score -= 25
            issues.append("Blacklist function - Wallets can be blocked")
        
        if ind.get('has_proxy_pattern', False):
            security_score -= 15
            issues.append("Proxy pattern - Contract can be changed")
        
        if ind.get('has_selfdestruct', False):
            security_score -= 30
            issues.append("Selfdestruct present - Contract can be destroyed")
        
        # Verification
        if not ind.get('contract_verified', False):
            security_score -= 10
            warnings.append("Contract not verified on explorer")
        
        # Honeypot
        if not ind.get('can_sell', True):
            security_score -= 50
            issues.append("HONEYPOT DETECTED - Cannot sell")
        
        if not ind.get('can_buy', True):
            security_score -= 50
            issues.append("Cannot buy - Trading blocked")
        
        return {
            "score": max(0, security_score),
            "issues": issues,
            "warnings": warnings,
            "is_honeypot": not ind.get('can_sell', True),
            "is_safe": security_score >= 70
        }
    
    def _analyze_liquidity(self, ind: dict, detection: dict) -> dict:
        """Analyse de liquidité"""
        liquidity_usd = detection.get('liquidity_usd', 0)
        
        # Score de liquidité
        if liquidity_usd >= 100000:
            liq_score = 100
            liq_level = "EXCELLENT"
        elif liquidity_usd >= 50000:
            liq_score = 85
            liq_level = "VERY_GOOD"
        elif liquidity_usd >= 25000:
            liq_score = 70
            liq_level = "GOOD"
        elif liquidity_usd >= 10000:
            liq_score = 55
            liq_level = "MEDIUM"
        elif liquidity_usd >= 5000:
            liq_score = 40
            liq_level = "LOW"
        else:
            liq_score = 20
            liq_level = "VERY_LOW"
        
        # LP Lock
        lp_locked = ind.get('lp_locked', False)
        lp_lock_days = ind.get('lp_lock_duration_days', 0)
        
        if lp_locked and lp_lock_days >= 365:
            lock_score = 100
        elif lp_locked and lp_lock_days >= 180:
            lock_score = 80
        elif lp_locked and lp_lock_days >= 90:
            lock_score = 60
        elif lp_locked:
            lock_score = 40
        else:
            lock_score = 0
        
        # Calcul de l'impact de prix
        price_impact_1_eth = self._calculate_price_impact(liquidity_usd, 2000) # 1 ETH
        price_impact_05_eth = self._calculate_price_impact(liquidity_usd, 1000) # 0.5 ETH
        
        return {
            "score": liq_score,
            "level": liq_level,
            "liquidity_usd": liquidity_usd,
            "lp_locked": lp_locked,
            "lp_lock_days": lp_lock_days,
            "lock_score": lock_score,
            "price_impact_1_eth": price_impact_1_eth,
            "price_impact_05_eth": price_impact_05_eth,
            "is_sufficient": liquidity_usd >= 10000,
            "rug_risk_liquidity": "HIGH" if not lp_locked else "LOW"
        }
    
    def _calculate_price_impact(self, liquidity_usd: float, trade_size_usd: float) -> float:
        """Calcule l'impact sur le prix"""
        if liquidity_usd == 0:
            return 100
        
        # Formule simplifiée d'AMM
        impact = (trade_size_usd / liquidity_usd) * 100
        return min(impact * 2, 100) # x2 car AMM curve
    
    def _analyze_momentum(self, ind: dict) -> dict:
        """Analyse du momentum"""
        # Volume et activité
        volume_5min = ind.get('volume_5min_usd', 0)
        buy_count = ind.get('buy_count_5min', 0)
        sell_count = ind.get('sell_count_5min', 0)
        unique_buyers = ind.get('unique_buyers_5min', 0)
        
        # Ratio acheteurs/vendeurs
        if sell_count > 0:
            buy_sell_ratio = buy_count / sell_count
        else:
            buy_sell_ratio = buy_count if buy_count > 0 else 1
        
        # Score de momentum
        momentum_score = 50
        
        if buy_sell_ratio > 3:
            momentum_score += 30
            momentum_level = "STRONG_BUY"
        elif buy_sell_ratio > 2:
            momentum_score += 20
            momentum_level = "BUY"
        elif buy_sell_ratio > 1:
            momentum_score += 10
            momentum_level = "MODERATE"
        elif buy_sell_ratio > 0.5:
            momentum_score -= 10
            momentum_level = "WEAK"
        else:
            momentum_score -= 20
            momentum_level = "SELL_PRESSURE"
        
        # Activité unique
        if unique_buyers > 50:
            momentum_score += 15
        elif unique_buyers > 20:
            momentum_score += 10
        elif unique_buyers < 5:
            momentum_score -= 10
        
        return {
            "score": min(max(momentum_score, 0), 100),
            "level": momentum_level,
            "buy_sell_ratio": round(buy_sell_ratio, 2),
            "volume_5min_usd": volume_5min,
            "unique_buyers": unique_buyers,
            "is_bullish": buy_sell_ratio > 1.5
        }
    
    def _calculate_risk_metrics(self, ind: dict, detection: dict) -> dict:
        """Calcul des métriques de risque"""
        
        # Distribution des tokens
        owner_balance_pct = ind.get('owner_balance_percent', 0)
        top10_pct = ind.get('top10_holders_percent', 0)
        holder_count = ind.get('holder_count', 0)
        
        # Concentration risk
        if owner_balance_pct > 20 or top10_pct > 70:
            concentration_risk = "HIGH"
        elif owner_balance_pct > 10 or top10_pct > 50:
            concentration_risk = "MEDIUM"
        else:
            concentration_risk = "LOW"
        
        # Age du token
        age_minutes = ind.get('age_minutes', 0)
        if age_minutes < 5:
            age_risk = "VERY_HIGH"
        elif age_minutes < 15:
            age_risk = "HIGH"
        elif age_minutes < 30:
            age_risk = "MEDIUM"
        else:
            age_risk = "LOW"
        
        # Taxes
        buy_tax = ind.get('buy_tax_real', 0)
        sell_tax = ind.get('sell_tax_real', 0)
        
        if buy_tax > 15 or sell_tax > 15:
            tax_risk = "HIGH"
        elif buy_tax > 10 or sell_tax > 10:
            tax_risk = "MEDIUM"
        else:
            tax_risk = "LOW"
        
        # Score de risque global
        risk_score = 0
        
        if concentration_risk == "HIGH":
            risk_score += 25
        elif concentration_risk == "MEDIUM":
            risk_score += 15
        
        if age_risk == "VERY_HIGH":
            risk_score += 20
        elif age_risk == "HIGH":
            risk_score += 10
        
        if tax_risk == "HIGH":
            risk_score += 15
        elif tax_risk == "MEDIUM":
            risk_score += 8
        
        return {
            "risk_score": min(risk_score, 100),
            "concentration_risk": concentration_risk,
            "age_risk": age_risk,
            "tax_risk": tax_risk,
            "owner_balance_percent": owner_balance_pct,
            "top10_holders_percent": top10_pct,
            "holder_count": holder_count,
            "buy_tax": buy_tax,
            "sell_tax": sell_tax
        }
    
    def _calculate_final_score(self, base, security, liquidity, momentum, risk) -> dict:
        """Calcul du score final pondéré"""
        
        # Pondérations
        weights = {
            "security": 0.35,
            "liquidity": 0.25,
            "momentum": 0.20,
            "profit_potential": 0.15,
            "risk": 0.05
        }
        
        # Scores
        security_score = security['score']
        liquidity_score = liquidity['score']
        momentum_score = momentum['score']
        profit_score = base['profit_potential']
        risk_score = 100 - risk['risk_score']
        
        # Score final
        final_score = (
            security_score * weights['security'] +
            liquidity_score * weights['liquidity'] +
            momentum_score * weights['momentum'] +
            profit_score * weights['profit_potential'] +
            risk_score * weights['risk']
        )
        
        # Niveau de confiance
        if security['is_honeypot']:
            confidence = 0
        elif security_score < 50:
            confidence = 20
        elif liquidity['liquidity_usd'] < 5000:
            confidence = 30
        else:
            confidence = min(95, 50 + (final_score / 2))
        
        return {
            "overall_score": round(final_score, 2),
            "security_score": security_score,
            "liquidity_score": liquidity_score,
            "momentum_score": momentum_score,
            "profit_score": profit_score,
            "risk_score": risk_score,
            "confidence": round(confidence, 2)
        }
    
    def _generate_trading_recommendation(self, final_score, security, liquidity, 
                                         momentum, risk, detection) -> dict:
        """Génère des recommandations de trading précises"""
        
        overall_score = final_score['overall_score']
        confidence = final_score['confidence']
        liquidity_usd = liquidity['liquidity_usd']
        price_usd = detection.get('price_usd', 0)
        
        # Décision de base
        if security['is_honeypot']:
            return self._honeypot_recommendation()
        
        if overall_score < 40:
            return self._avoid_recommendation(overall_score, security, risk)
        
        if overall_score >= 75 and confidence >= 70:
            return self._aggressive_buy_recommendation(
                liquidity_usd, price_usd, liquidity, momentum, risk, detection
            )
        
        if overall_score >= 60 and confidence >= 60:
            return self._moderate_buy_recommendation(
                liquidity_usd, price_usd, liquidity, momentum, risk, detection
            )
        
        if overall_score >= 45:
            return self._cautious_buy_recommendation(
                liquidity_usd, price_usd, liquidity, momentum, risk, detection
            )
        
        return self._monitor_recommendation(overall_score, security, liquidity)
    
    def _aggressive_buy_recommendation(self, liq_usd, price, liq_analysis, momentum, risk, detection):
        """Recommandation d'achat agressif"""
        
        # Calcul de la taille de position
        if liq_usd >= 100000:
            position_size_eth = 1.0
            position_size_usd = 2000
        elif liq_usd >= 50000:
            position_size_eth = 0.5
            position_size_usd = 1000
        elif liq_usd >= 25000:
            position_size_eth = 0.3
            position_size_usd = 600
        else:
            position_size_eth = 0.2
            position_size_usd = 400
        
        # Calcul des niveaux de prix
        entry_price = price
        take_profit_1 = entry_price * 1.5 # +50%
        take_profit_2 = entry_price * 2.0 # +100%
        take_profit_3 = entry_price * 3.0 # +200%
        stop_loss = entry_price * 0.85 # -15%
        
        # Stratégie de sortie
        exit_strategy = [
            {"level": "TP1 (+50%)", "price": take_profit_1, "sell_percent": 30, "reason": "Secure initial profit"},
            {"level": "TP2 (+100%)", "price": take_profit_2, "sell_percent": 40, "reason": "Take major profit"},
            {"level": "TP3 (+200%)", "price": take_profit_3, "sell_percent": 30, "reason": "Moon bag"},
        ]
        
        # Timing
        entry_timing = "IMMEDIATE - dans les 30 secondes"
        hold_duration = "2-6 heures (scalping)"
        
        # Risque
        max_loss_usd = position_size_usd * 0.15
        potential_gain_usd = position_size_usd * 1.0 # 100% average
        risk_reward_ratio = potential_gain_usd / max_loss_usd
        
        return {
            "action": "BUY_AGGRESSIVE",
            "confidence": "TRÈS ÉLEVÉE (85-95%)",
            "position_sizing": {
                "amount_eth": position_size_eth,
                "amount_usd": position_size_usd,
                "max_slippage": "3-5%",
                "gas_priority": "HIGH"
            },
            "entry": {
                "timing": entry_timing,
                "price_target": entry_price,
                "price_range_min": entry_price * 0.97,
                "price_range_max": entry_price * 1.03,
                "method": "Market order with slippage protection"
            },
            "exit_strategy": exit_strategy,
            "stop_loss": {
                "price": stop_loss,
                "percent": -15,
                "type": "Hard stop (automatic)"
            },
            "hold_duration": hold_duration,
            "risk_management": {
                "max_loss_usd": round(max_loss_usd, 2),
                "potential_gain_usd": round(potential_gain_usd, 2),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "portfolio_allocation": "5-8%"
            },
            "warnings": [
                f"Prix impact pour cette taille: {liq_analysis['price_impact_05_eth']:.2f}%",
                f"Liquidité totale: ${liq_usd:,.0f}",
                "Token très récent - Risque de volatilité extrême",
                "Surveiller les premières minutes pour détecter un rug"
            ],
            "monitoring": {
                "check_frequency": "Toutes les 30 secondes",
                "key_metrics": ["Prix", "Volume", "Holder count", "Top holders"],
                "red_flags": [
                    "Owner vend plus de 5% du supply",
                    "Chute de liquidité > 20%",
                    "Volume de vente > 3x volume d'achat"
                ]
            }
        }
    
    def _moderate_buy_recommendation(self, liq_usd, price, liq_analysis, momentum, risk, detection):
        """Recommandation d'achat modéré"""
        
        # Position plus petite
        if liq_usd >= 50000:
            position_size_eth = 0.3
            position_size_usd = 600
        elif liq_usd >= 25000:
            position_size_eth = 0.2
            position_size_usd = 400
        else:
            position_size_eth = 0.15
            position_size_usd = 300
        
        entry_price = price
        take_profit_1 = entry_price * 1.3
        take_profit_2 = entry_price * 1.8
        take_profit_3 = entry_price * 2.5
        stop_loss = entry_price * 0.90
        
        exit_strategy = [
            {"level": "TP1 (+30%)", "price": take_profit_1, "sell_percent": 40, "reason": "Secure early profit"},
            {"level": "TP2 (+80%)", "price": take_profit_2, "sell_percent": 40, "reason": "Take profit"},
            {"level": "TP3 (+150%)", "price": take_profit_3, "sell_percent": 20, "reason": "Let winners run"},
        ]
        
        max_loss_usd = position_size_usd * 0.10
        potential_gain_usd = position_size_usd * 0.6
        
        return {
            "action": "BUY_MODERATE",
            "confidence": "ÉLEVÉE (70-85%)",
            "position_sizing": {
                "amount_eth": position_size_eth,
                "amount_usd": position_size_usd,
                "max_slippage": "2-3%",
                "gas_priority": "MEDIUM"
            },
            "entry": {
                "timing": "Dans les 1-2 minutes - observer d'abord",
                "price_target": entry_price,
                "price_range_min": entry_price * 0.98,
                "price_range_max": entry_price * 1.02,
                "method": "Limit order recommandé"
            },
            "exit_strategy": exit_strategy,
            "stop_loss": {
                "price": stop_loss,
                "percent": -10,
                "type": "Trailing stop recommandé"
            },
            "hold_duration": "4-12 heures",
            "risk_management": {
                "max_loss_usd": round(max_loss_usd, 2),
                "potential_gain_usd": round(potential_gain_usd, 2),
                "risk_reward_ratio": round(potential_gain_usd / max_loss_usd, 2),
                "portfolio_allocation": "3-5%"
            },
            "warnings": [
                f"Prix impact: {liq_analysis['price_impact_05_eth']:.2f}%",
                "Attendre confirmation du momentum",
                "Vérifier qu'il n'y a pas de dumping immédiat"
            ],
            "monitoring": {
                "check_frequency": "Toutes les 5 minutes",
                "key_metrics": ["Volume trend", "Holder growth", "LP changes"],
                "red_flags": [
                    "Volume décroissant rapidement",
                    "Concentration augmente",
                    "Liquidity unlocks"
                ]
            }
        }
    
    def _cautious_buy_recommendation(self, liq_usd, price, liq_analysis, momentum, risk, detection):
        """Recommandation d'achat prudent"""
        
        position_size_eth = 0.1
        position_size_usd = 200
        
        entry_price = price
        take_profit_1 = entry_price * 1.2
        take_profit_2 = entry_price * 1.5
        stop_loss = entry_price * 0.92
        
        exit_strategy = [
            {"level": "TP1 (+20%)", "price": take_profit_1, "sell_percent": 50, "reason": "Quick profit"},
            {"level": "TP2 (+50%)", "price": take_profit_2, "sell_percent": 50, "reason": "Exit completely"},
        ]
        
        return {
            "action": "BUY_CAUTIOUS",
            "confidence": "MOYENNE (60-70%)",
            "position_sizing": {
                "amount_eth": position_size_eth,
                "amount_usd": position_size_usd,
                "max_slippage": "2%",
                "gas_priority": "LOW"
            },
            "entry": {
                "timing": "Attendre 5-10 minutes pour confirmation",
                "price_target": entry_price,
                "price_range_min": entry_price * 0.95,
                "price_range_max": entry_price * 1.05,
                "method": "Small limit order"
            },
            "exit_strategy": exit_strategy,
            "stop_loss": {
                "price": stop_loss,
                "percent": -8,
                "type": "Strict stop loss"
            },
            "hold_duration": "2-6 heures max",
            "risk_management": {
                "max_loss_usd": 16.0,
                "potential_gain_usd": 70.0,
                "risk_reward_ratio": 4.4,
                "portfolio_allocation": "1-2%"
            },
            "warnings": [
                "Risques élevés détectés",
                "Position test uniquement",
                "Sortir rapidement en cas de signaux négatifs"
            ],
            "monitoring": {
                "check_frequency": "Constant (toutes les minutes)",
                "key_metrics": ["Immediate price action", "Selling pressure"],
                "red_flags": ["Any suspicious activity"]
            }
        }
    
    def _monitor_recommendation(self, score, security, liquidity):
        """Recommandation de surveillance"""
        return {
            "action": "MONITOR",
            "confidence": "FAIBLE (<60%)",
            "recommendation": "NE PAS ACHETER - Surveiller seulement",
            "reasons": [
                f"Score global trop faible: {score}/100",
                f"Sécurité: {security['score']}/100",
                f"Liquidité: {liquidity['score']}/100"
            ],
            "what_to_watch": [
                "Augmentation de la liquidité",
                "Croissance des holders",
                "Amélioration du momentum",
                "Renonciation du owner"
            ],
            "reconsider_if": [
                "Liquidité > $25,000",
                "LP locked for 90+ days",
                "Owner renounced",
                "Buying momentum increases"
            ]
        }
    
    def _avoid_recommendation(self, score, security, risk):
        """Recommandation d'éviter"""
        return {
            "action": "AVOID",
            "confidence": "TRÈS ÉLEVÉE (90%+)",
            "recommendation": "❌ NE PAS ACHETER - ÉVITER COMPLÈTEMENT",
            "critical_issues": security['issues'],
            "risk_level": "TRÈS ÉLEVÉ",
            "reasons": [
                f"Score trop bas: {score}/100",
                f"Problèmes de sécurité critiques: {len(security['issues'])}"
            ]
        }
    
    def _honeypot_recommendation(self):
        """Recommandation pour honeypot"""
        return {
            "action": "AVOID_HONEYPOT",
            "confidence": "100%",
            "recommendation": "🚨 HONEYPOT DÉTECTÉ - NE JAMAIS ACHETER 🚨",
            "critical_warning": "Vous ne pourrez PAS vendre ce token !",
            "loss_probability": "100%"
        }
