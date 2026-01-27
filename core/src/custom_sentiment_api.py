"""
LENS sentiment analysis API client.
Uses local LENS sentiment analysis service for crypto news analysis.
"""
import requests
from typing import Dict, Optional, List


class LensSentimentAPI:
    """Client for LENS sentiment analysis API."""
    
    def __init__(self, api_url: str = "http://192.168.0.73:8765/analyze"):
        """
        Initialize LENS sentiment API client.
        
        Args:
            api_url: URL of the LENS sentiment analysis API endpoint
        """
        self.api_url = api_url
    
    def analyze_crypto(self, symbol: str, time_range: str = "day", top_k: int = 30) -> Optional[Dict]:
        """
        Analyze sentiment for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
            time_range: Time range for articles ("day", "week", "month")
            top_k: Number of articles to analyze
            
        Returns:
            Dictionary with sentiment analysis or None if error:
            {
                'symbol': str,
                'sentiment': str ('positive', 'negative', 'neutral'),
                'confidence': float,
                'positive_pct': float,
                'negative_pct': float,
                'neutral_pct': float,
                'article_count': int
            }
        """
        try:
            # Build query string
            query = f"{symbol} crypto coin"
            
            payload = {
                "query": query,
                "time_range": time_range,
                "top_k": top_k
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=300,  # 5 minute timeout for LENS API
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            overall_sentiment = data.get('overall_sentiment', 'NEUTRAL').lower()
            percentages = data.get('percentages', {})
            
            positive_pct = percentages.get('positive', 0)
            negative_pct = percentages.get('negative', 0)
            neutral_pct = percentages.get('neutral', 0)
            
            # Determine sentiment based on positive vs negative
            if positive_pct > negative_pct:
                if positive_pct >= 50:
                    sentiment = 'hype'  # Strong positive sentiment
                else:
                    sentiment = 'excitement'  # Moderate positive sentiment
            elif negative_pct > positive_pct:
                if negative_pct >= 50:
                    sentiment = 'fearful'  # Strong negative sentiment
                else:
                    sentiment = 'doubt'  # Moderate negative sentiment
            else:
                sentiment = 'neutral'
            
            return {
                'symbol': symbol,
                'sentiment': sentiment,
                'confidence': data.get('confidence', 0),
                'positive_pct': positive_pct,
                'negative_pct': negative_pct,
                'neutral_pct': neutral_pct,
                'article_count': data.get('article_count', 0),
                'reasoning': f"Analyzed {data.get('article_count', 0)} articles: {positive_pct:.0f}% positive, {negative_pct:.0f}% negative, {neutral_pct:.0f}% neutral"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  LENS API error for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"   ⚠️  Error parsing LENS response for {symbol}: {e}")
            return None
    
    def analyze_multiple_cryptos(self, crypto_list: List[Dict], verbose: bool = True) -> List[Dict]:
        """
        Analyze sentiment for multiple cryptocurrencies.
        
        Args:
            crypto_list: List of crypto dictionaries with 'symbol' or 'name' field
            verbose: Whether to print progress
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        
        for crypto in crypto_list:
            # Extract symbol name (remove exchange prefix and USDT suffix)
            symbol_raw = crypto.get('symbol', crypto.get('name', 'UNKNOWN'))
            symbol = symbol_raw.split(':')[-1].replace('USDT', '').replace('/', '')
            
            if verbose:
                print(f"   Analyzing {symbol}...")
            
            sentiment_result = self.analyze_crypto(symbol)
            
            if sentiment_result:
                results.append(sentiment_result)
                if verbose:
                    emoji_map = {
                        'hype': '🔥',
                        'excitement': '🚀',
                        'neutral': '😐',
                        'doubt': '🤔',
                        'fearful': '😨'
                    }
                    emoji = emoji_map.get(sentiment_result['sentiment'], '❓')
                    print(f"      {emoji} {sentiment_result['sentiment'].upper()} "
                          f"({sentiment_result['positive_pct']:.0f}% pos, "
                          f"{sentiment_result['negative_pct']:.0f}% neg)")
            else:
                # Return unknown if API fails
                results.append({
                    'symbol': symbol,
                    'sentiment': 'unknown',
                    'confidence': 0,
                    'positive_pct': 0,
                    'negative_pct': 0,
                    'neutral_pct': 0,
                    'article_count': 0,
                    'reasoning': 'LENS API unavailable'
                })
                if verbose:
                    print(f"      ❓ UNKNOWN (LENS API error)")
        
        return results


def main():
    """Test the LENS sentiment API."""
    api = LensSentimentAPI()
    
    print("Testing LENS Sentiment API")
    print("=" * 60)
    
    # Test single crypto
    result = api.analyze_crypto("BTC")
    if result:
        print(f"\nBitcoin Sentiment:")
        print(f"  Sentiment: {result['sentiment']}")
        print(f"  Confidence: {result['confidence']:.1f}%")
        print(f"  Positive: {result['positive_pct']:.1f}%")
        print(f"  Negative: {result['negative_pct']:.1f}%")
        print(f"  Neutral: {result['neutral_pct']:.1f}%")
        print(f"  Articles: {result['article_count']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
