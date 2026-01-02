"""Risk Management System"""
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, config):
        self.max_position_size_usd = config.get("MAX_POSITION_SIZE_USD", 500)
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None

    def calculate_position_size(self, portfolio_value_usd, rug_risk_score, strategy):
        if rug_risk_score > 80:
            return 0

        if rug_risk_score < 25:
            base_percent = 6
        elif rug_risk_score < 40:
            base_percent = 4
        elif rug_risk_score < 55:
            base_percent = 2
        elif rug_risk_score < 70:
            base_percent = 1
        else:
            base_percent = 0.8

        if strategy == "scalping":
            base_percent *= 0.8
        elif strategy == "momentum":
            base_percent *= 1.1

        amount_usd = portfolio_value_usd * (base_percent / 100)
        return min(amount_usd, self.max_position_size_usd)

    def check_circuit_breaker(self, stats):
        if self.circuit_breaker_active and datetime.utcnow() < self.circuit_breaker_until:
            return {"should_pause": True, "mode": "PAUSE"}

        if stats.get("consecutive_losses", 0) >= 3:
            self._activate_circuit_breaker(60)
            return {"should_pause": True, "mode": "PAUSE"}

        return {"should_pause": False, "mode": "NORMAL"}

    def _activate_circuit_breaker(self, duration_minutes):
        self.circuit_breaker_active = True
        self.circuit_breaker_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
