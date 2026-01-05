"""Discord Notification System"""
import logging
import aiohttp

logger = logging.getLogger(__name__)

class DiscordNotifier:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
        
        if self.enabled:
            logger.info("✅ Discord notifications enabled")
        else:
            logger.info("ℹ️ Discord notifications disabled (no webhook)")
    
    async def send_detection_alert(self, detection: dict, analysis: dict):
        """Envoie une alerte Discord"""
        if not self.enabled:
            return
        
        try:
            recommendation = analysis['trading_recommendation']
            action = recommendation['action']
            
            # Couleur selon action
            if action == "BUY_AGGRESSIVE":
                color = 0x00FF00
            elif action in ["BUY_MODERATE", "BUY_CAUTIOUS"]:
                color = 0xFFFF00
            else:
                color = 0xFF0000
            
            embed = {
                "title": f"🎯 {detection.get('name', 'N/A')} ({detection.get('symbol', 'N/A')})",
                "description": f"Nouveau token détecté sur {detection['chain']}",
                "color": color,
                "fields": [
                    {"name": "Score", "value": f"{analysis['final_score']['overall_score']:.1f}/100", "inline": True},
                    {"name": "Liquidité", "value": f"${detection.get('liquidity_usd', 0):,.0f}", "inline": True},
                    {"name": "Action", "value": action, "inline": False},
                    {"name": "Adresse", "value": detection['token_address'], "inline": False}
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json={"embeds": [embed]})
            
            logger.info(f"✅ Discord alert sent")
            
        except Exception as e:
            logger.error(f"❌ Discord error: {e}")
