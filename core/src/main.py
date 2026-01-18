"""
Main entry point for Miletus crypto trading analysis.
"""
import os
from tradingview_screener import TradingViewScreener
from telegram_notifier import TelegramNotifier
from tavily_crypto_query import TavilyCryptoQuery


def main():
    """Main application entry point."""
    print("=" * 160)
    print("MILETUS - AI Crypto Trading Software")
    print("=" * 160)
    print()
    
    # Step 1: Scan TradingView for technical opportunities
    print("Step 1: Scanning TradingView for technical opportunities...")
    print("-" * 160)
    
    # Initialize screener without CSV output (can be changed to True if needed)
    screener = TradingViewScreener(save_to_csv=False)
    
    # Scan for cryptocurrencies
    tv_results = screener.scan(
        min_volume_usd=1_000_000,      # Min $1M volume
        min_volume_change=10,           # Min +10% volume change
        max_volume_change=500,          # Max 500% to avoid manipulation
        tech_ratings=["BUY", "STRONG_BUY"],  # Bullish ratings only
        limit=100,                      # Fetch up to 100 from API
        max_results=10,                 # Return only top 10 best results
        verbose=True
    )
    
    print("\n" + "=" * 160)
    print(f"Found {len(tv_results)} cryptocurrencies with strong technicals")
    print("=" * 160)
    
    # Step 2: Analyze sentiment for top 10 results
    sentiment_results = []
    if tv_results:
        print("\nStep 2: Analyzing sentiment for top 10 cryptocurrencies...")
        print("-" * 160)
        
        try:
            tavily = TavilyCryptoQuery()
            top_10 = tv_results[:10]
            
            sentiment_results = tavily.analyze_multiple_cryptos(top_10, verbose=True)
            
            # Display sentiment results
            print("\n" + "=" * 160)
            print("SENTIMENT ANALYSIS RESULTS")
            print("=" * 160)
            
            sentiment_emojis = {
                'fearful': '😨',
                'excitement': '🚀',
                'doubt': '🤔',
                'hype': '🔥',
                'neutral': '😐',
                'unknown': '❓'
            }
            
            for result in sentiment_results:
                emoji = sentiment_emojis.get(result['sentiment'], '❓')
                print(f"{emoji} {result['symbol']}: {result['sentiment'].upper()}")
                if result.get('reasoning'):
                    print(f"   Reasoning: {result['reasoning'][:150]}...")
            
            print("=" * 160)
            
            # Enrich tv_results with sentiment and reasoning
            for i, tv_result in enumerate(top_10):
                if i < len(sentiment_results):
                    tv_result['sentiment'] = sentiment_results[i]['sentiment']
                    tv_result['sentiment_reasoning'] = sentiment_results[i].get('reasoning', '')
            
        except Exception as e:
            print(f"⚠️  Sentiment analysis skipped: {e}")
            print("    Set TAVILY_API environment variable to enable sentiment analysis")
    
    # Step 3: Send Telegram notification if results found
    if tv_results:
        print("\n📱 Sending Telegram notification...")
        try:
            notifier = TelegramNotifier(
                bot_token=os.getenv("TELEGRAM_KEY"),
                chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
            success = notifier.send_crypto_alert_sync(tv_results[:10])  # Send top 10 with sentiment
            if success:
                print("✅ Telegram notification sent successfully!")
            else:
                print("⚠️  Telegram notification failed. Make sure TELEGRAM_CHAT_ID is set.")
                print("   To get your chat ID, message your bot and run:")
                print("   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        except Exception as e:
            print(f"⚠️  Telegram notification error: {e}")
    
    print("\n" + "=" * 160)
    print("Analysis complete!")
    print("=" * 160)
    
    # Return results for further processing if needed
    return {
        'tradingview': tv_results,
        'sentiment': sentiment_results
    }


if __name__ == "__main__":
    main()
