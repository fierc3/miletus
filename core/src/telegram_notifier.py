"""
Telegram bot notifier for sending crypto trading alerts.
"""
import os
import asyncio
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError


class TelegramNotifier:
    """Send notifications via Telegram bot."""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token. If None, reads from TELEGRAM_KEY env var
            chat_id: Telegram chat ID. If None, reads from TELEGRAM_CHAT_ID env var
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_KEY")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            raise ValueError("Telegram bot token not provided and TELEGRAM_KEY not set")
        
        self.bot = Bot(token=self.bot_token)
    
    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message: Message text to send
            parse_mode: Telegram parse mode (Markdown, HTML, or None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.chat_id:
            print("Warning: No chat_id configured. Cannot send Telegram message.")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Synchronous wrapper for send_message.
        
        Args:
            message: Message text to send
            parse_mode: Telegram parse mode (Markdown, HTML, or None)
            
        Returns:
            True if successful, False otherwise
        """
        return asyncio.run(self.send_message(message, parse_mode))
    
    def format_crypto_results(self, results: List[Dict]) -> str:
        """
        Format cryptocurrency results for Telegram message.
        
        Args:
            results: List of cryptocurrency dictionaries from TradingView screener
            
        Returns:
            Formatted message string
        """
        if not results:
            return "🔍 *Crypto Trading Alert*\n\nNo cryptocurrencies found matching criteria."
        
        message = "🚀 *Crypto Trading Alert*\n\n"
        message += f"Found *{len(results)}* promising cryptocurrencies:\n\n"
        
        sentiment_emojis = {
            'fearful': '😨',
            'excitement': '🚀',
            'doubt': '🤔',
            'hype': '🔥',
            'neutral': '😐',
            'unknown': '❓'
        }
        
        for idx, crypto in enumerate(results[:10], 1):  # Limit to top 10
            symbol = crypto.get('symbol', 'N/A').replace(':', ' - ')
            price = crypto.get('price', 0)
            change_pct = crypto.get('change_pct', 0)
            volume = crypto.get('volume', 0)
            volume_change = crypto.get('volume_change', 0)
            tech_rating = crypto.get('tech_rating', 'N/A')
            rsi = crypto.get('rsi', 0)
            sentiment = crypto.get('sentiment', None)
            
            # Format emoji based on rating
            rating_emoji = "💚" if tech_rating == "STRONG_BUY" else "🟢" if tech_rating == "BUY" else "⚪"
            
            message += f"{rating_emoji} *{idx}. {symbol}*\n"
            message += f"   Price: ${price:.6f}\n"
            message += f"   Change: {change_pct:+.2f}%\n"
            message += f"   Volume: ${volume:,.0f}\n"
            message += f"   Vol Change: {volume_change:+.1f}%\n"
            message += f"   Rating: {tech_rating}\n"
            message += f"   RSI: {rsi:.1f}\n"
            
            # Add sentiment if available
            if sentiment:
                sentiment_emoji = sentiment_emojis.get(sentiment, '❓')
                message += f"   Sentiment: {sentiment_emoji} {sentiment.upper()}\n"
                
                # Add reasoning if available
                reasoning = crypto.get('sentiment_reasoning', '')
                if reasoning:
                    # Truncate for Telegram
                    if len(reasoning) > 150:
                        reasoning = reasoning[:147] + "..."
                    # Escape Markdown special characters to prevent parsing errors
                    reasoning = reasoning.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
                    message += f"   _{reasoning}_\n"
            
            message += "\n"
        
        if len(results) > 10:
            message += f"_...and {len(results) - 10} more_\n\n"
        
        message += "📊 *Criteria:*\n"
        message += "• Volume: > $1M\n"
        message += "• Vol Change: 10-500%\n"
        message += "• Rating: BUY/STRONG BUY\n"
        message += "• Sentiment: News analysis\n"
        
        return message
    
    async def send_crypto_alert(self, results: List[Dict]) -> bool:
        """
        Send cryptocurrency trading alert.
        
        Args:
            results: List of cryptocurrency dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        message = self.format_crypto_results(results)
        return await self.send_message(message)
    
    def send_crypto_alert_sync(self, results: List[Dict]) -> bool:
        """
        Synchronous wrapper for send_crypto_alert.
        
        Args:
            results: List of cryptocurrency dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return asyncio.run(self.send_crypto_alert(results))


def main():
    """Test the Telegram notifier."""
    # Example usage
    notifier = TelegramNotifier()
    
    # Test message
    test_results = [
        {
            'symbol': 'BINANCE:BTCUSDT',
            'name': 'Bitcoin',
            'price': 45000.50,
            'change_pct': 5.2,
            'volume': 1500000000,
            'volume_change': 15.5,
            'tech_rating': 'STRONG_BUY',
            'rsi': 65.3
        }
    ]
    
    success = notifier.send_crypto_alert_sync(test_results)
    if success:
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send test message")


if __name__ == "__main__":
    main()
