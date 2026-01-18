"""
TradingView Screener with custom filters for cryptocurrency discovery.
Filters: Volume > 1M USD, Galaxy Score > 70, Sentiment 70%+, Tech Rating Buy/Strong Buy
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
import json


class TradingViewScreener:
    """Search TradingView for cryptocurrencies with specific filters."""
    
    def __init__(self, save_to_csv: bool = False, csv_filename: str = "tradingview_screener_results.csv"):
        """
        Initialize the TradingView screener.
        
        Args:
            save_to_csv: Whether to save results to CSV file (default: False)
            csv_filename: Name of CSV file to save results (default: tradingview_screener_results.csv)
        """
        self.base_url = "https://scanner.tradingview.com/crypto/scan"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
        }
        self.save_to_csv = save_to_csv
        self.csv_filename = csv_filename
    
    def search_cryptos(self,
                      min_volume_usd: float = 1_000_000,
                      min_galaxy_score: float = 70,
                      min_sentiment: float = 70,
                      min_volume_change: float = 10,
                      max_volume_change: float = 500,
                      tech_ratings: List[str] = ["BUY", "STRONG_BUY"],
                      limit: int = 100) -> Optional[List[Dict]]:
        """
        Search TradingView for cryptocurrencies matching filters.
        
        Args:
            min_volume_usd: Minimum 24h volume in USD (default: 1M)
            min_galaxy_score: Minimum Galaxy Score (default: 70)
            min_sentiment: Minimum sentiment percentage (default: 70)
            min_volume_change: Minimum volume change percentage (default: 10%)
            max_volume_change: Maximum volume change to avoid manipulation (default: 500%)
            tech_ratings: Accepted technical ratings (default: BUY, STRONG_BUY)
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of cryptocurrencies matching criteria
        """
        # Build filters list
        filters = [
            # Volume > min_volume_usd
            {"left": "volume", "operation": "greater", "right": min_volume_usd},
            # Tech Rating: Buy or Strong Buy (Recommend.All > 0.1 for Buy, > 0.5 for Strong Buy)
            {"left": "Recommend.All", "operation": "greater", "right": 0.1},
            # Volume change >= 10%
            {"left": "change_from_open|1", "operation": "greater", "right": min_volume_change},
            # Volume change <= 500% (avoid manipulation)
            {"left": "change_from_open|1", "operation": "less", "right": max_volume_change}
        ]
        
        # Build the TradingView scanner payload
        payload = {
            "filter": filters,
            "options": {
                "lang": "en"
            },
            "symbols": {
                "query": {
                    "types": []
                },
                "tickers": []
            },
            "columns": [
                "name",
                "close",
                "change",
                "volume",
                "change_from_open|1",
                "Recommend.All",
                "RSI",
                "market_cap_basic"
            ],
            "sort": {
                "sortBy": "change_from_open|1",
                "sortOrder": "desc"
            },
            "range": [0, limit]
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                results = self._parse_results(data, tech_ratings)
                
                # Filter to only USDT pairs (more reputable)
                filtered_results = []
                for result in results:
                    symbol = result['symbol']
                    # Only include USDT pairs, and exclude tokens with underscores (often scam tokens)
                    if 'USDT' in symbol.upper() and '_' not in symbol:
                        filtered_results.append(result)
                
                return filtered_results[:limit]
            else:
                print(f"Error: API returned status code {response.status_code}")
                try:
                    print(f"Response: {response.text[:500]}")
                except:
                    pass
                return None
                
        except Exception as e:
            print(f"Error searching TradingView: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_results(self, data: Dict, tech_ratings: List[str]) -> List[Dict]:
        """Parse TradingView API response."""
        results = []
        
        if 'data' not in data:
            return results
        
        for item in data['data']:
            try:
                symbol_info = item['s']
                values = item['d']
                
                # Map column values: name, close, change, volume, change_from_open|1, Recommend.All, RSI, market_cap_basic
                result = {
                    'symbol': symbol_info,
                    'name': values[0] if len(values) > 0 else '',
                    'price': values[1] if len(values) > 1 else 0,
                    'change_pct': values[2] if len(values) > 2 else 0,
                    'volume': values[3] if len(values) > 3 else 0,
                    'volume_change': values[4] if len(values) > 4 else 0,
                    'recommend_score': values[5] if len(values) > 5 else 0,
                    'rsi': values[6] if len(values) > 6 else 0,
                    'market_cap': values[7] if len(values) > 7 else 0,
                }
                
                # Convert recommend score to rating
                rec_score = result['recommend_score']
                if rec_score >= 0.5:
                    result['tech_rating'] = 'STRONG_BUY'
                elif rec_score >= 0.1:
                    result['tech_rating'] = 'BUY'
                elif rec_score >= -0.1:
                    result['tech_rating'] = 'NEUTRAL'
                elif rec_score >= -0.5:
                    result['tech_rating'] = 'SELL'
                else:
                    result['tech_rating'] = 'STRONG_SELL'
                
                # Filter by tech rating
                if result['tech_rating'] in tech_ratings:
                    results.append(result)
                    
            except Exception as e:
                continue
        
        return results
    
    def display_results(self, results: List[Dict], verbose: bool = True):
        """
        Display results in a formatted table.
        
        Args:
            results: List of cryptocurrency results
            verbose: Whether to print the results table (default: True)
            
        Returns:
            DataFrame with formatted results or None if no results
        """
        if not results:
            if verbose:
                print("No cryptocurrencies found matching criteria.")
            return None
        
        df = pd.DataFrame(results)
        
        # Save to CSV if requested
        if self.save_to_csv:
            df.to_csv(self.csv_filename, index=False)
            if verbose:
                print(f"✅ Results saved to '{self.csv_filename}'")
        
        if verbose:
            # Format columns for display
            df_display = df.copy()
            df_display['volume'] = df_display['volume'].apply(lambda x: f"${x:,.0f}" if x else "N/A")
            df_display['price'] = df_display['price'].apply(lambda x: f"${x:.4f}" if x else "N/A")
            df_display['change_pct'] = df_display['change_pct'].apply(lambda x: f"{x:+.2f}%" if x is not None else "N/A")
            df_display['volume_change'] = df_display['volume_change'].apply(lambda x: f"{x:+.1f}%" if x is not None else "N/A")
            df_display['rsi'] = df_display['rsi'].apply(lambda x: f"{x:.1f}" if x is not None else "N/A")
            df_display['market_cap'] = df_display['market_cap'].apply(lambda x: f"${x:,.0f}" if (x and x > 0) else "N/A")
            
            # Reorder columns
            display_cols = ['symbol', 'name', 'price', 'change_pct', 'volume', 'volume_change',
                           'tech_rating', 'rsi', 'market_cap']
            df_display = df_display[display_cols]
            
            print("\n" + "=" * 160)
            print(f"Found {len(results)} cryptocurrencies matching criteria")
            print("=" * 160)
            print(df_display.to_string(index=False))
            print("=" * 160)
        
        return df
    
    def scan(self,
             min_volume_usd: float = 1_000_000,
             min_volume_change: float = 10,
             max_volume_change: float = 500,
             tech_ratings: List[str] = ["BUY", "STRONG_BUY"],
             limit: int = 100,
             max_results: int = None,
             verbose: bool = True) -> List[Dict]:
        """
        Main method to scan for cryptocurrencies matching criteria.
        
        Args:
            min_volume_usd: Minimum 24h volume in USD (default: 1M)
            min_volume_change: Minimum volume change percentage (default: 10%)
            max_volume_change: Maximum volume change to avoid manipulation (default: 500%)
            tech_ratings: Accepted technical ratings (default: BUY, STRONG_BUY)
            limit: Maximum number of results to fetch from API (default: 100)
            max_results: Maximum results to return after sorting (default: None = all)
            verbose: Whether to print progress and results (default: True)
            
        Returns:
            List of cryptocurrency dictionaries with all fields, sorted by rating
        """
        if verbose:
            print("Searching TradingView for cryptocurrencies...")
        
        results = self.search_cryptos(
            min_volume_usd=min_volume_usd,
            min_volume_change=min_volume_change,
            max_volume_change=max_volume_change,
            tech_ratings=tech_ratings,
            limit=limit
        )
        
        if results:
            # Sort by tech rating (STRONG_BUY first, then BUY)
            # Then by volume change (higher is better)
            rating_priority = {'STRONG_BUY': 0, 'BUY': 1, 'NEUTRAL': 2, 'SELL': 3, 'STRONG_SELL': 4}
            results.sort(
                key=lambda x: (
                    rating_priority.get(x.get('tech_rating', 'NEUTRAL'), 999),
                    -x.get('volume_change', 0)  # Negative for descending order
                )
            )
            
            # Limit results if max_results is specified
            if max_results and len(results) > max_results:
                if verbose:
                    print(f"Limiting results to top {max_results} (sorted by STRONG_BUY first, then volume change)")
                results = results[:max_results]
            
            self.display_results(results, verbose=verbose)
            return results
        else:
            if verbose:
                print("❌ Failed to retrieve results from TradingView")
                print("This could be due to:")
                print("  • API rate limiting")
                print("  • Network connectivity issues")
                print("  • No cryptocurrencies matching the strict filters")
                print("\nTry running the standalone script for more details:")
                print("  cd core && uv run python src/tradingview_screener.py")
            return []


def main():
    """Main entry point for TradingView screener standalone usage."""
    print("=" * 160)
    print("TRADINGVIEW CRYPTOCURRENCY SCREENER")
    print("=" * 160)
    print("\nSearch Filters:")
    print("• Volume: > $1M USD")
    print("• Volume Change: >= +10% (shows early trend)")
    print("• Volume Change: <= 500% (avoids manipulation)")
    print("• Tech Rating: BUY or STRONG BUY")
    print("\n" + "=" * 160)
    print("\nNote: Galaxy Score and Sentiment filters require TradingView premium API access.")
    print("Currently filtering by Volume, Volume Change, and Tech Rating.")
    print("\n" + "=" * 160 + "\n")
    
    # Initialize screener with CSV output enabled
    screener = TradingViewScreener(save_to_csv=True, csv_filename="tradingview_screener_results.csv")
    
    # Scan for cryptocurrencies
    results = screener.scan(
        min_volume_usd=1_000_000,
        min_volume_change=10,
        max_volume_change=500,
        tech_ratings=["BUY", "STRONG_BUY"],
        limit=100,
        verbose=True
    )
    
    print(f"\n✅ Found {len(results)} cryptocurrencies matching criteria")
    print()


if __name__ == "__main__":
    main()
