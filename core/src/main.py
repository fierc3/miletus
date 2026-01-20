"""
Main entry point for Miletus crypto trading analysis.
"""
import os
from tradingview_screener import TradingViewScreener
from telegram_notifier import TelegramNotifier
from tavily_crypto_query import TavilyCryptoQuery
from binance_trader import BinanceTrader


def main():
    """Main application entry point."""
    # ASCII Art Banner
    print("""
                     @@@@@@@@  @@@@@@@@
                 @@@@   -@@@@@@@@@@@   @@@@
               @@@   @@@            @@@   @@@
            @@@   @@@                  @@@   @@@
          @@@    @@         @@@@         @@    @@@
         @@    @@       @@@@    @@@@       @@    @@
       @@@    @@      @@  @      @  @@      @@    @@@
      @@      @     @@                @@     @      @@
     @@      @@    %@ @  +@@@@@@@@@  @ @@    @@      @@
    @@       @     @@     @@@@@@@@     @@     @       @@
   @@        @     @@     @@@@@@@@     @@     @        @@
    @@       @     @@     @@@@@@@@     @@     @       @@
     @@      @@    .@ @  =@@@@@@@@*  @ @+    @@      @@
      @@      @     @@                @@     @      @@
       @@@    @@      @@  @      @  @@      @@    @@@
         @@    @@       @@@@    @@@@       @@    @@
          @@@    @@         @@@@         @@    @@@
            @@@   @@@                  @@@   @@@
               @@@   @@@            @@@   @@@
                 @@@@    @@@@@@@@@@    @@@@
                     @@@@@@@@  @@@@@@@@
    """)
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
    
    # Step 3: Execute trades on Binance if trading is enabled
    trading_enabled = os.getenv("BINANCE_TRADING_ENABLED", "false").lower() == "true"
    successful_trades = []
    
    if tv_results and trading_enabled:
        print("\n" + "=" * 160)
        print("Step 3: Executing trades on Binance...")
        print("-" * 160)
        
        try:
            # Initialize Binance trader
            trader = BinanceTrader(
                testnet=True)
            
            # Get investment amount from env var (default: $100)
            usdt_amount = float(os.getenv("BINANCE_TRADE_AMOUNT_USDT", "100"))
            
            # Get TP/SL ranges from env vars with defaults
            tp_min = float(os.getenv("BINANCE_TP_MIN", "5"))
            tp_max = float(os.getenv("BINANCE_TP_MAX", "15"))
            sl_min = float(os.getenv("BINANCE_SL_MIN", "2"))
            sl_max = float(os.getenv("BINANCE_SL_MAX", "5"))
            
            print(f"Trading Settings:")
            print(f"  • Amount per trade: ${usdt_amount} USDT")
            print(f"  • Take Profit: +{tp_min}% to +{tp_max}%")
            print(f"  • Stop Loss: -{sl_min}% to -{sl_max}%")
            print()
            
            # Try to trade each crypto in the results list
            for idx, crypto in enumerate(tv_results):
                original_symbol = crypto['symbol']
                
                # Convert symbol format: "BINANCE:BTCUSDT" or "GATE:WORKUSDT" -> "BTCUSDT"
                # Remove exchange prefix and any slashes
                symbol = original_symbol.split(':')[-1].replace('/', '')
                
                print(f"🎯 Attempting to trade #{idx + 1}: {symbol}")
                print(f"   Original Symbol: {original_symbol}")
                print(f"   Technical Rating: {crypto.get('tech_rating', 'N/A')}")
                if 'sentiment' in crypto:
                    print(f"   Sentiment: {crypto['sentiment']}")
                print()
                
                result = trader.place_market_buy_with_tp_sl(
                    symbol=symbol,
                    usdt_amount=usdt_amount,
                    tp_percent_min=tp_min,
                    tp_percent_max=tp_max,
                    sl_percent_min=sl_min,
                    sl_percent_max=sl_max
                )
                
                if result['success']:
                    print(f"✅ Trade executed successfully!")
                    print(f"   Entry Price: ${result['entry_price']:.8f}")
                    print(f"   Quantity: {result['quantity']}")
                    print(f"   Take Profit: ${result['tp_price']:.8f} (+{result['tp_percent']:.2f}%)")
                    print(f"   Stop Loss: ${result['sl_price']:.8f} ({result['sl_percent']:.2f}%)")
                    print()
                    
                    # Add to successful trades with full crypto info
                    successful_trades.append(crypto)
                else:
                    print(f"⚠️  Skipping {symbol}: {result['message']}")
                    print()
            
            if successful_trades:
                print("=" * 160)
                print(f"✅ Successfully executed {len(successful_trades)} trade(s)")
                print("=" * 160)
            else:
                print("=" * 160)
                print("⚠️  No trades were executed")
                print("=" * 160)
            
        except ValueError as e:
            print(f"⚠️  Binance trading disabled: {e}")
            print("    Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables to enable trading")
        except Exception as e:
            print(f"⚠️  Binance trading error: {e}")
    elif tv_results and not trading_enabled:
        print("\n" + "=" * 160)
        print("💡 Binance trading is DISABLED")
        print("   Set BINANCE_TRADING_ENABLED=true to enable automatic trading")
        print("=" * 160)
    
    # Step 4: Send Telegram notification if successful trades were made
    if successful_trades:
        print("\n📱 Sending Telegram notification for successful trades...")
        try:
            notifier = TelegramNotifier(
                bot_token=os.getenv("TELEGRAM_KEY"),
                chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
            success = notifier.send_crypto_alert_sync(successful_trades)
            if success:
                print("✅ Telegram notification sent successfully!")
            else:
                print("⚠️  Telegram notification failed. Make sure TELEGRAM_CHAT_ID is set.")
                print("   To get your chat ID, message your bot and run:")
                print("   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        except Exception as e:
            print(f"⚠️  Telegram notification error: {e}")
    elif trading_enabled and not successful_trades:
        print("\n📱 No successful trades to notify about")
    
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
