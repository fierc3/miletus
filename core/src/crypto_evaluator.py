"""
Cryptocurrency technical evaluation using TradingView TA and CCXT.
Filters cryptocurrencies based on technical indicators and volume criteria.
"""
import ccxt
import pandas as pd
from tradingview_ta import TA_Handler, Interval
from typing import List, Dict, Optional
import time


class CryptoEvaluator:
    """Evaluates cryptocurrencies based on technical indicators and volume."""
    
    def __init__(self, exchange_id: str = "binance"):
        """
        Initialize the crypto evaluator.
        
        Args:
            exchange_id: Exchange to use for data (default: binance)
        """
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
        })
        
    def get_technical_analysis(self, symbol: str, screener: str = "crypto", 
                               exchange: str = "BINANCE", interval: str = "1h") -> Optional[Dict]:
        """
        Get technical analysis for a cryptocurrency using TradingView TA.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            screener: TradingView screener type
            exchange: TradingView exchange name
            interval: Time interval for analysis
            
        Returns:
            Dictionary with technical analysis data or None if failed
        """
        try:
            # Format symbol for TradingView (remove slash if present)
            tv_symbol = symbol.replace("/", "")
            
            handler = TA_Handler(
                symbol=tv_symbol,
                screener=screener,
                exchange=exchange,
                interval=interval
            )
            
            analysis = handler.get_analysis()
            return {
                'summary': analysis.summary,
                'oscillators': analysis.oscillators,
                'moving_averages': analysis.moving_averages,
                'indicators': analysis.indicators
            }
        except Exception as e:
            print(f"Error getting technical analysis for {symbol}: {e}")
            return None
    
    def get_volume_data(self, symbol: str) -> Optional[Dict]:
        """
        Get volume data from CCXT exchange.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            
        Returns:
            Dictionary with volume data or None if failed
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # Get 24h volume in quote currency (usually USDT)
            volume_24h = ticker.get('quoteVolume', 0)
            
            return {
                'volume_24h': volume_24h,
                'base_volume': ticker.get('baseVolume', 0),
                'quote_volume': ticker.get('quoteVolume', 0),
            }
        except Exception as e:
            print(f"Error getting volume data for {symbol}: {e}")
            return None
    
    def evaluate_crypto(self, symbol: str, 
                       min_volume: float = 3_000_000,
                       rsi_min: float = 55,
                       rsi_max: float = 69,
                       rsi_overbought: float = 70,
                       min_volume_change: float = 10,
                       max_volume_spike: float = 500) -> Dict:
        """
        Evaluate a cryptocurrency against all criteria.
        
        Criteria:
        - Technical Rating is "Strong Buy"
        - RSI (14) is between 55-69 (bullish but not overbought)
        - Volume Change is +10% or more (shows early trend)
        - Avoid RSI above 70 (overbought)
        - Avoid volume spikes above 500% (manipulation risk)
        - Minimum 24h Volume: $3M+ (safe liquidity)
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            min_volume: Minimum 24h volume in USD (default: 3M)
            rsi_min: Minimum RSI value (default: 55)
            rsi_max: Maximum RSI value (default: 69)
            rsi_overbought: RSI overbought threshold (default: 70)
            min_volume_change: Minimum volume change % (default: 10)
            max_volume_spike: Maximum volume spike % (default: 500)
            
        Returns:
            Dictionary with evaluation results and detailed metrics
        """
        result = {
            'symbol': symbol,
            'passed': False,
            'criteria_met': {},
            'metrics': {},
            'recommendation': '',
            'reasons': []
        }
        
        # Get technical analysis
        ta_data = self.get_technical_analysis(symbol)
        if not ta_data:
            result['reasons'].append("Failed to get technical analysis")
            return result
        
        # Get volume data
        volume_data = self.get_volume_data(symbol)
        if not volume_data:
            result['reasons'].append("Failed to get volume data")
            return result
        
        # Extract key metrics
        tech_rating = ta_data['summary']['RECOMMENDATION']
        rsi = ta_data['indicators'].get('RSI', 0)
        volume_24h = volume_data['volume_24h']
        
        # Try to calculate volume change from recent data
        try:
            # Fetch OHLCV data for volume change calculation
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=2)
            if len(ohlcv) >= 2:
                prev_volume = ohlcv[-2][5]  # Previous day volume
                current_volume = ohlcv[-1][5]  # Current day volume
                volume_change_pct = ((current_volume - prev_volume) / prev_volume) * 100 if prev_volume > 0 else 0
            else:
                volume_change_pct = 0
        except:
            volume_change_pct = 0
        
        # Store metrics
        result['metrics'] = {
            'tech_rating': tech_rating,
            'rsi': rsi,
            'volume_24h': volume_24h,
            'volume_change_pct': volume_change_pct,
        }
        
        # Evaluate each criterion
        criteria = {}
        
        # 1. Technical Rating is "Strong Buy"
        criteria['strong_buy'] = tech_rating == "STRONG_BUY"
        if not criteria['strong_buy']:
            result['reasons'].append(f"Tech rating is '{tech_rating}', not 'STRONG_BUY'")
        
        # 2. RSI between 55-69
        criteria['rsi_range'] = rsi_min <= rsi <= rsi_max
        if not criteria['rsi_range']:
            result['reasons'].append(f"RSI {rsi:.2f} not in range {rsi_min}-{rsi_max}")
        
        # 3. RSI not overbought (< 70)
        criteria['not_overbought'] = rsi < rsi_overbought
        if not criteria['not_overbought']:
            result['reasons'].append(f"RSI {rsi:.2f} is overbought (>= {rsi_overbought})")
        
        # 4. Volume change >= 10%
        criteria['volume_increase'] = volume_change_pct >= min_volume_change
        if not criteria['volume_increase']:
            result['reasons'].append(f"Volume change {volume_change_pct:.2f}% < {min_volume_change}%")
        
        # 5. Volume spike not above 500%
        criteria['no_manipulation'] = volume_change_pct <= max_volume_spike
        if not criteria['no_manipulation']:
            result['reasons'].append(f"Volume spike {volume_change_pct:.2f}% suggests manipulation (> {max_volume_spike}%)")
        
        # 6. Minimum 24h volume
        criteria['sufficient_liquidity'] = volume_24h >= min_volume
        if not criteria['sufficient_liquidity']:
            result['reasons'].append(f"Volume ${volume_24h:,.0f} < ${min_volume:,.0f}")
        
        result['criteria_met'] = criteria
        
        # Determine if all criteria are met
        result['passed'] = all(criteria.values())
        
        if result['passed']:
            result['recommendation'] = "BUY - All criteria met"
            result['reasons'] = ["Meets all technical and volume criteria"]
        elif not result['reasons']:
            result['recommendation'] = "HOLD - Review criteria"
        else:
            result['recommendation'] = "SKIP - Criteria not met"
        
        return result
    
    def evaluate_multiple(self, symbols: List[str], **kwargs) -> pd.DataFrame:
        """
        Evaluate multiple cryptocurrencies and return results as DataFrame.
        
        Args:
            symbols: List of trading pair symbols
            **kwargs: Additional arguments to pass to evaluate_crypto()
            
        Returns:
            Pandas DataFrame with evaluation results
        """
        results = []
        
        for symbol in symbols:
            print(f"Evaluating {symbol}...")
            result = self.evaluate_crypto(symbol, **kwargs)
            results.append(result)
            
            # Rate limiting
            time.sleep(self.exchange.rateLimit / 1000)
        
        # Convert to DataFrame
        df_data = []
        for r in results:
            row = {
                'Symbol': r['symbol'],
                'Passed': r['passed'],
                'Recommendation': r['recommendation'],
                'Tech Rating': r['metrics'].get('tech_rating', 'N/A'),
                'RSI': r['metrics'].get('rsi', 0),
                'Volume 24h': r['metrics'].get('volume_24h', 0),
                'Volume Change %': r['metrics'].get('volume_change_pct', 0),
                'Reasons': ' | '.join(r['reasons'])
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        return df


    def discover_all_cryptos(self, quote_currency: str = "USDT",
                            min_volume_filter: float = 3_000_000) -> List[str]:
        """
        Discover all available cryptocurrencies on the exchange.
        
        Args:
            quote_currency: Quote currency to filter by (default: USDT)
            min_volume_filter: Pre-filter by minimum volume to reduce API calls
            
        Returns:
            List of trading pair symbols that meet minimum volume
        """
        print(f"Discovering all {quote_currency} pairs on exchange...")
        
        try:
            # Load markets
            self.exchange.load_markets()
            
            # Get all USDT pairs
            all_symbols = [symbol for symbol in self.exchange.symbols
                          if quote_currency in symbol and symbol.endswith(f'/{quote_currency}')]
            
            print(f"Found {len(all_symbols)} {quote_currency} pairs")
            print(f"Pre-filtering by minimum volume ${min_volume_filter:,.0f}...")
            
            # Pre-filter by volume to reduce API calls
            viable_symbols = []
            for symbol in all_symbols:
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    volume_24h = ticker.get('quoteVolume', 0)
                    
                    if volume_24h >= min_volume_filter:
                        viable_symbols.append(symbol)
                    
                    # Rate limiting
                    time.sleep(self.exchange.rateLimit / 1000)
                except Exception as e:
                    continue
            
            print(f"Found {len(viable_symbols)} pairs with volume >= ${min_volume_filter:,.0f}")
            return viable_symbols
            
        except Exception as e:
            print(f"Error discovering cryptocurrencies: {e}")
            return []


def main():
    """Main entry point for discovering and evaluating cryptocurrencies."""
    # Initialize evaluator
    evaluator = CryptoEvaluator(exchange_id="binance")
    
    print("=" * 100)
    print("CRYPTOCURRENCY DISCOVERY & TECHNICAL EVALUATION")
    print("=" * 100)
    print("\nCriteria:")
    print("• Tech Rating: Strong Buy")
    print("• RSI (14): 55-69 (bullish but not overbought)")
    print("• Volume Change: +10% or more")
    print("• Avoid RSI > 70 (overbought)")
    print("• Avoid volume spikes > 500%")
    print("• Minimum 24h Volume: $3M+")
    print("\n" + "=" * 100 + "\n")
    
    # Discover all viable cryptocurrencies
    symbols = evaluator.discover_all_cryptos(quote_currency="USDT", min_volume_filter=3_000_000)
    
    if not symbols:
        print("No cryptocurrencies found meeting minimum volume criteria.")
        return
    
    print(f"\nEvaluating {len(symbols)} cryptocurrencies...")
    print("This may take a while due to API rate limits...\n")
    
    # Evaluate all discovered symbols
    results_df = evaluator.evaluate_multiple(symbols)
    
    # Sort by RSI and Volume for better insights
    results_df_sorted = results_df.sort_values(by='Volume 24h', ascending=False)
    
    # Display only cryptocurrencies that pass all criteria
    passed = results_df_sorted[results_df_sorted['Passed'] == True]
    
    if not passed.empty:
        print("\n" + "=" * 100)
        print(f"🎯 DISCOVERED {len(passed)} CRYPTOCURRENCIES MEETING ALL CRITERIA:")
        print("=" * 100)
        print(passed.to_string(index=False))
        
        # Save to CSV for further analysis
        passed.to_csv('discovered_cryptos.csv', index=False)
        print(f"\n✅ Results saved to 'discovered_cryptos.csv'")
    else:
        print("\n" + "=" * 100)
        print("❌ No cryptocurrencies currently meet all criteria.")
        print("=" * 100)
        
        # Show top candidates that nearly meet criteria
        print("\n📊 TOP 10 CANDIDATES (by volume):")
        print("-" * 100)
        top_candidates = results_df_sorted.head(10)
        print(top_candidates.to_string(index=False))
    
    # Save all results for analysis
    results_df_sorted.to_csv('all_crypto_evaluations.csv', index=False)
    print(f"\n📁 All evaluations saved to 'all_crypto_evaluations.csv'")
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
