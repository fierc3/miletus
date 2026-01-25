import requests
import json
from typing import List, Dict, Optional

class TradingViewScanner:
    """
    High-performance TradingView scanner using the official API.
    """
    
    def __init__(self):
        self.url = "https://scanner.tradingview.com/crypto/scan"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        }

    def scan(self,
             min_volume_usd: float = 500_000,
             min_volume_change: float = 5.0, # 5% = 1.05 Relative Volume
             max_volume_change: float = 500.0,
             tech_ratings: List[str] = ["BUY", "STRONG_BUY", "NEUTRAL"],
             max_symbols: int = 50,
             max_results: int = 20,
             verbose: bool = True) -> List[Dict]:
        
        # 1. Calculate Relative Volume (RVol)
        # If market is quiet, RVol might be 0.8 or 0.9.
        # We set a floor of 0.5 to ensure we at least get data, 
        # unless user specifically asks for a pump (>0).
        if min_volume_change > 0:
            min_rvol = 1.0 + (min_volume_change / 100.0)
        else:
            min_rvol = None # Disable filter if 0 or negative passed
        
        # Calculate max rvol for upper bound filtering
        max_rvol = 1.0 + (max_volume_change / 100.0) if max_volume_change > 0 else None

        if verbose:
            rvol_range = f"RVol: {min_rvol if min_rvol else 'Any'} to {max_rvol if max_rvol else 'Any'}"
            print(f"   🔍 Scanning BINANCE (Vol > ${min_volume_usd:,.0f}, {rvol_range})...")

        # 2. Define Columns
        columns = [
            "name", "close", "change", "24h_vol|5", 
            "relative_volume_10d_calc", "Recommend.All", "RSI", "exchange"
        ]

        # 3. Build Filters
        # Note: We use "match" for exchange to be safer than "equal"
        filter_conditions = [
            {"left": "exchange", "operation": "match", "right": "BINANCE"},
            {"left": "name", "operation": "match", "right": "USDT"}, 
            {"left": "24h_vol|5", "operation": "greater", "right": min_volume_usd},
            {"left": "name", "operation": "nmatch", "right": "USDC"}, # Exclude stable pairs
            {"left": "name", "operation": "nmatch", "right": "BUSD"},
            {"left": "name", "operation": "nmatch", "right": "DAI"},
            {"left": "name", "operation": "nmatch", "right": "DOWN"},
            {"left": "name", "operation": "nmatch", "right": "UP"},
            {"left": "name", "operation": "nmatch", "right": "SEED"}  # Exclude SEED listings (high risk new tokens)
        ]
        
        if min_rvol:
            filter_conditions.append(
                {"left": "relative_volume_10d_calc", "operation": "greater", "right": min_rvol}
            )
        
        if max_rvol:
            filter_conditions.append(
                {"left": "relative_volume_10d_calc", "operation": "less", "right": max_rvol}
            )

        payload = {
            "filter": filter_conditions,
            "options": {"lang": "en"},
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": columns,
            "sort": {"sortBy": "relative_volume_10d_calc", "sortOrder": "desc"},
            "range": [0, max_symbols * 2] # Fetch double to allow for local filtering
        }

        try:
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload), timeout=10)
            data = response.json()
        except Exception as e:
            print(f"   ❌ API Connection Error: {e}")
            return []

        if not data or 'data' not in data:
            if verbose: print("   ⚠️  TradingView returned 0 raw results. Market might be very quiet.")
            return []
        
        if verbose:
            print(f"   📊 TradingView API returned {len(data['data'])} raw candidates.")

        results = []
        for item in data['data']:
            d = item['d']
            
            # Extract
            symbol_raw = d[0]
            price = d[1]
            price_change = d[2]
            volume_usd = d[3]
            rvol = d[4] if d[4] is not None else 1.0
            rating_score = d[5] if d[5] is not None else 0
            rsi = d[6] if d[6] is not None else 50

            # Map Rating
            rating = "NEUTRAL"
            if rating_score >= 0.5: rating = "STRONG_BUY"
            elif rating_score >= 0.1: rating = "BUY"
            elif rating_score <= -0.5: rating = "STRONG_SELL"
            elif rating_score <= -0.1: rating = "SELL"

            # Filter Ratings
            if rating not in tech_ratings:
                continue

            # Append
            results.append({
                'symbol': f"BINANCE:{symbol_raw}", 
                'name': symbol_raw,
                'price': price,
                'change_pct': price_change,
                'volume': volume_usd,
                'volume_change': (rvol - 1) * 100, # Display as % change from avg
                'relative_volume': rvol,
                'tech_rating': rating,
                'recommend_score': rating_score,
                'rsi': rsi
            })

        if verbose and len(results) == 0:
            print("   ⚠️  Results were found but filtered out by 'tech_ratings' locally.")

        return results[:max_results]