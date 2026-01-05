"""Telegram Notification System"""
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        
        if self.enabled:
            logger.info("✅ Telegram notifications enabled")
        else:
            logger.info("ℹ️ Telegram notifications disabled (no credentials)")
    
    async def send_detection_alert(self, detection: dict, analysis: dict):
        """Envoie une alerte de détection"""
        if not self.enabled:
            return
        
        try:
            # Import dynamique pour éviter l'erreur si pas installé
            from telegram import Bot
            
            bot = Bot(token=self.bot_token)
            
            recommendation = analysis['trading_recommendation']
            action = recommendation['action']
            
            message = f"🎯 <b>NOUVEAU TOKEN</b>\n\n"
            message += f"<b>Token:</b> {detection.get('name', 'N/A')} ({detection.get('symbol', 'N/A')})\n"
            message += f"<b>Chain:</b> {detection['chain']}\n"
            message += f"<b>Action:</b> {action}\n"
            message += f"<b>Score:</b> {analysis['final_score']['overall_score']:.1f}/100\n"
            message += f"\n<code>{detection['token_address']}</code>"
            
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Telegram alert sent")
            
        except ImportError:
            logger.warning("⚠️ python-telegram-bot not installed")
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")
    
    async def send_trade_execution(self, trade_info: dict):
        """Notification de trade"""
        if not self.enabled:
            return
        
        try:
            from telegram import Bot
            
            bot = Bot(token=self.bot_token)
            
            message = f"✅ <b>TRADE EXÉCUTÉ</b>\n\n"
            message += f"<b>Token:</b> {trade_info['symbol']}\n"
            message += f"<b>Action:</b> {trade_info['action']}\n"
            message += f"<b>Montant:</b> {trade_info['amount']} ETH\n"
            
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    async def send_alert(self, message: str, level: str = "INFO"):
        """Alerte générale"""
        if not self.enabled:
            return
        
        try:
            from telegram import Bot
            
            bot = Bot(token=self.bot_token)
            emoji = "ℹ️" if level == "INFO" else "⚠️" if level == "WARNING" else "🚨"
            
            await bot.send_message(
                chat_id=self.chat_id,
                text=f"{emoji} {message}"
            )
        except Exception as e:
            logger.error(f"❌ Error: {e}")
