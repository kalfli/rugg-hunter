"""Scalping Strategy"""
class ScalpingStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.name = "scalping"
        self.config = {
            "max_rug_risk": 40,
            "min_liquidity_usd": 15000,
            "min_profit_potential": 60,
            "stop_loss_percent": -12
        }

    def should_enter(self, analysis):
        if analysis["rug_risk_score"] >= self.config["max_rug_risk"]:
            return False, "Rug risk too high"
        if analysis["indicators"]["liquidity_usd"] < self.config["min_liquidity_usd"]:
            return False, "Liquidity too low"
        return True, "Entry conditions met"

    def should_exit(self, position, current_data):
        if current_data.get("rug_signal_detected"):
            return True, "RUG_SIGNAL", 100
        pnl = position.get("unrealized_pnl_percent", 0)
        if pnl >= 25:
            return True, "TAKE_PROFIT_25%", 40
        if pnl <= self.config["stop_loss_percent"]:
            return True, "STOP_LOSS", 100
        return False, "", 0
