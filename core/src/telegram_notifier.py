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
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters for Telegram."""
        # Escape Markdown V1 special characters
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        return text
    
    def format_crypto_results(self, results: List[Dict]) -> str:
        """
        Format cryptocurrency results for Telegram message.
        
        Args:
            results: List of cryptocurrency dictionaries from trades
            
        Returns:
            Formatted message string
        """
        if not results:
            return "🔍 *Crypto Trading Alert*\n\nNo cryptocurrencies found matching criteria."
        
        message = "✅ *TRADES EXECUTED*\n\n"
        message += f"Successfully placed *{len(results)}* trades:\n\n"
        
        sentiment_emojis = {
            'fearful': '😨',
            'excitement': '🚀',
            'doubt': '🤔',
            'hype': '🔥',
            'neutral': '😐',
            'unknown': '❓'
        }
        
        for idx, crypto in enumerate(results, 1):
            symbol = crypto.get('name', crypto.get('symbol', 'N/A')).replace('USDT', '')
            entry_price = crypto.get('entry_price', crypto.get('price', 0))
            quantity = crypto.get('quantity', 0)
            tp_price = crypto.get('tp_price', 0)
            sl_price = crypto.get('sl_price', 0)
            tp_percent = crypto.get('tp_percent', 0)
            sl_percent = crypto.get('sl_percent', 0)
            tech_rating = crypto.get('tech_rating', 'N/A')
            sentiment = crypto.get('sentiment', None)
            is_partial = crypto.get('partial_fill', False)
            
            # Format emoji based on rating
            rating_emoji = "💚" if tech_rating == "STRONG_BUY" else "🟢" if tech_rating == "BUY" else "⚪"
            
            # Calculate position value
            position_value = entry_price * quantity if entry_price and quantity else 0
            
            # Escape all text fields for markdown
            safe_symbol = self._escape_markdown(symbol)
            safe_rating = self._escape_markdown(tech_rating)
            
            message += f"{rating_emoji} *{idx}\\. {safe_symbol}*\n"
            message += f"   💰 Entry: ${entry_price:.6f}\n"
            message += f"   📦 Quantity: {quantity:.2f}\n"
            message += f"   💵 Position: ${position_value:.2f}\n"
            
            if is_partial:
                message += f"   ⚠️ PARTIAL FILL \\- OCO FAILED\n"
                message += f"   ⚠️ Manual TP/SL required\n"
            else:
                message += f"   🎯 TP: ${tp_price:.6f} \\(\\+{tp_percent:.1f}%\\)\n"
                message += f"   🛑 SL: ${sl_price:.6f} \\({sl_percent:.1f}%\\)\n"
            
            message += f"   📊 Rating: {safe_rating}\n"
            
            # Add sentiment if available
            if sentiment:
                sentiment_emoji = sentiment_emojis.get(sentiment, '❓')
                safe_sentiment = self._escape_markdown(sentiment.upper())
                message += f"   🧠 Sentiment: {sentiment_emoji} {safe_sentiment}\n"
            
            message += "\n"
        
        message += "━━━━━━━━━━━━━━━━━\n"
        message += "💡 Orders are OCO (One-Cancels-Other)\n"
        message += "When TP hits, SL cancels automatically\n"
        
        return message
    
    def format_error_results(self, errors: List[Dict]) -> str:
        """
        Format error results for Telegram message.
        
        Args:
            errors: List of error dictionaries from failed trades
            
        Returns:
            Formatted error message string
        """
        if not errors:
            return "⚠️ *TRADE ERRORS*\n\nNo errors to report."
        
        message = "🚨 *TRADE ERRORS*\n\n"
        message += f"Failed to execute *{len(errors)}* trade(s):\n\n"
        
        for idx, error in enumerate(errors, 1):
            symbol = error.get('symbol', 'N/A').replace('USDT', '')
            error_msg = error.get('error', 'Unknown error')
            is_partial = error.get('partial_fill', False)
            
            # Escape for markdown
            safe_symbol = self._escape_markdown(symbol)
            safe_error = self._escape_markdown(error_msg)
            
            if is_partial:
                # CRITICAL: Buy succeeded but OCO failed
                entry_price = error.get('entry_price', 0)
                quantity = error.get('quantity', 0)
                buy_order_id = error.get('buy_order_id', 'N/A')
                tp_percent = error.get('tp_percent', 10)
                sl_percent = error.get('sl_percent', 3.5)
                
                # Calculate what TP/SL should have been
                tp_price = entry_price * (1 + tp_percent / 100) if entry_price else 0
                sl_price = entry_price * (1 - sl_percent / 100) if entry_price else 0
                
                message += f"🚨 *{idx}\\. {safe_symbol}* \\- CRITICAL\n"
                message += f"   ⚠️ BUY SUCCEEDED but OCO FAILED\n"
                message += f"   💰 Entry: ${entry_price:.6f}\n"
                message += f"   📦 Quantity: {quantity:.2f}\n"
                message += f"   🆔 Order ID: {buy_order_id}\n"
                message += f"   \n"
                message += f"   *Manual TP/SL needed:*\n"
                message += f"   🎯 TP: ${tp_price:.6f} \\(\\+{tp_percent:.1f}%\\)\n"
                message += f"   🛑 SL: ${sl_price:.6f} \\(\\-{sl_percent:.1f}%\\)\n"
                message += f"   \n"
                message += f"   ❌ Error: {safe_error}\n"
                message += f"   ⚠️ Set TP/SL manually ASAP\\!\n"
            else:
                # Normal failure (buy didn't execute)
                message += f"❌ *{idx}\\. {safe_symbol}*\n"
                message += f"   Error: {safe_error}\n"
            
            message += "\n"
        
        message += "━━━━━━━━━━━━━━━━━\n"
        message += "💡 Check logs for more details\n"
        
        return message
    
    async def send_error_alert(self, errors: List[Dict]) -> bool:
        """
        Send error alert for failed trades.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        message = self.format_error_results(errors)
        return await self.send_message(message)
    
    def send_error_alert_sync(self, errors: List[Dict]) -> bool:
        """
        Synchronous wrapper for send_error_alert.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return asyncio.run(self.send_error_alert(errors))
    
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
