"""
Main entry point for Miletus crypto trading analysis.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from tradingview_screener_v2 import TradingViewScanner
from telegram_notifier import TelegramNotifier
from tavily_crypto_query import TavilyCryptoQuery
from binance_trader import BinanceTrader
from fear_greed_index import FearGreedIndex

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


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
    
    # Step 0: Check Fear & Greed Index
    print("Step 0: Checking market sentiment via Fear & Greed Index...")
    print("-" * 160)
    
    fgi = FearGreedIndex()
    fear_greed_data = fgi.get_current_index()
    
    if fear_greed_data:
        print(fgi.format_report(fear_greed_data))
        fear_greed_value = fear_greed_data['value']
        
        # Check if market conditions are too extreme (Extreme Greed > 75)
        if fear_greed_value > 75:
            print("⚠️  WARNING: Extreme Greed detected!")
            print("   Market may be overheated. Consider reducing position sizes or waiting.")
            print()
    else:
        print("⚠️  Could not fetch Fear & Greed Index, continuing without it...")
        fear_greed_value = 50  # Default to neutral if unavailable
    
    print("\n" + "=" * 160)
    
    # Step 1: Scan TradingView for technical opportunities
    # Step 1: Scan TradingView for technical opportunities
    print("Step 1: Scanning TradingView for technical opportunities...")
    print("-" * 160)
    
    # Initialize new library-based screener
    screener = TradingViewScanner()
    
    # Scan for cryptocurrencies
    tv_results = screener.scan(
        min_volume_usd=500_000,         # Min $500K volume
        min_volume_change=0,            # No minimum volume change (include all)
        max_volume_change=500.0,        # Max 500% to avoid manipulation
        tech_ratings=["BUY", "STRONG_BUY", "NEUTRAL"],  # Include NEUTRAL ratings
        max_symbols=50,                 # Analyze top 50 pairs by volume
        max_results=20,                 # Return top 20 results
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
    failed_trades = []  # Track failed trades for error notifications
    
    if tv_results and trading_enabled:
        print("\n" + "=" * 160)
        print("Step 3: Executing trades on Binance...")
        print("-" * 160)
        
        try:
            # Initialize Binance trader
            use_testnet = os.getenv("BINANCE_USE_TESTNET", "true").lower() == "true"
            trader = BinanceTrader(testnet=use_testnet)
            
            if use_testnet:
                print("⚠️  Using Binance TESTNET (fake money)")
            else:
                print("🚨 Using Binance PRODUCTION (REAL MONEY)")
            print()
            
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
            
            # Filter 1: Check Fear & Greed Index - skip trading if Extreme Greed
            if fear_greed_value > 75:
                print(f"⚠️  Extreme Greed ({fear_greed_value}/100) - Skipping all trades to avoid overheated market")
                print("=" * 160)
                print("⚠️  No trades were executed due to extreme market conditions")
                print("=" * 160)
            else:
                # Filter 2: Sentiment filtering based on technical rating
                # - STRONG_BUY: excitement, hype, OR neutral allowed
                # - BUY/NEUTRAL: only excitement or hype (neutral sentiment not enough)
                
                for idx, crypto in enumerate(tv_results):
                    original_symbol = crypto['symbol']
                    tech_rating = crypto.get('tech_rating', 'NEUTRAL')
                    crypto_sentiment = crypto.get('sentiment', 'unknown')
                    
                    # Check sentiment filter based on rating
                    if tech_rating == 'STRONG_BUY':
                        allowed_sentiments = {'excitement', 'hype', 'neutral'}
                    else:  # BUY or NEUTRAL rating
                        allowed_sentiments = {'excitement', 'hype'}
                    
                    if crypto_sentiment not in allowed_sentiments:
                        print(f"⏭️  Skipping #{idx + 1}: {original_symbol} - {tech_rating} requires {allowed_sentiments} sentiment, got '{crypto_sentiment}'")
                        continue
                    
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
                        
                        # Merge crypto info with trade result for Telegram notification
                        trade_info = {
                            **crypto,  # Include TradingView data (sentiment, rating, etc.)
                            **result   # Add trade execution data (entry_price, quantity, tp, sl)
                        }
                        successful_trades.append(trade_info)
                    else:
                        print(f"⚠️  Skipping {symbol}: {result['message']}")
                        print()
                        
                        # Track failed trade for error notification
                        failed_info = {
                            'symbol': symbol,
                            'original_symbol': original_symbol,
                            'error': result['message'],
                            'partial_fill': result.get('partial_fill', False),
                            'buy_order_id': result.get('buy_order_id'),
                            'entry_price': result.get('entry_price'),
                            'quantity': result.get('quantity')
                        }
                        failed_trades.append(failed_info)
                        
                        # If partial fill (buy succeeded), also add to successful trades for logging
                        if result.get('partial_fill', False):
                            partial_trade_info = {
                                **crypto,
                                'symbol': symbol,
                                'entry_price': result.get('entry_price'),
                                'quantity': result.get('quantity'),
                                'tp_price': 0,  # No TP/SL since OCO failed
                                'sl_price': 0,
                                'tp_percent': 0,
                                'sl_percent': 0,
                                'partial_fill': True
                            }
                            successful_trades.append(partial_trade_info)
                
                if successful_trades:
                    print("=" * 160)
                    # Count actual full successes vs partial fills
                    full_success = sum(1 for t in successful_trades if not t.get('partial_fill', False))
                    partial_success = sum(1 for t in successful_trades if t.get('partial_fill', False))
                    
                    if partial_success > 0:
                        print(f"✅ Successfully executed {full_success} trade(s)")
                        print(f"⚠️  {partial_success} trade(s) partially filled (buy succeeded but OCO failed)")
                    else:
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
    
    # Step 4: Send Telegram notifications
    if successful_trades or failed_trades:
        try:
            notifier = TelegramNotifier(
                bot_token=os.getenv("TELEGRAM_KEY"),
                chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
            
            # Send both notifications in a single async context to avoid event loop issues
            import asyncio
            
            async def send_all_notifications():
                results = []
                
                if successful_trades:
                    print("\n📱 Sending Telegram notification for successful trades...")
                    success = await notifier.send_crypto_alert(successful_trades)
                    results.append(('success', success))
                
                if failed_trades:
                    print("🚨 Sending Telegram error notification...")
                    error_success = await notifier.send_error_alert(failed_trades)
                    results.append(('error', error_success))
                
                return results
            
            notification_results = asyncio.run(send_all_notifications())
            
            # Report results
            for notif_type, success in notification_results:
                if notif_type == 'success':
                    if success:
                        print("✅ Success notification sent!")
                    else:
                        print("⚠️  Success notification failed.")
                elif notif_type == 'error':
                    if success:
                        print("✅ Error notification sent!")
                    else:
                        print("⚠️  Error notification failed.")
                    
        except Exception as e:
            print(f"⚠️  Telegram notification error: {e}")
    elif trading_enabled and not successful_trades and not failed_trades:
        print("\n📱 No trades to notify about")
    
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
