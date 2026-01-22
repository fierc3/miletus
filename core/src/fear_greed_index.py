"""
Fear & Greed Index fetcher for crypto market sentiment.
Uses the Alternative.me Crypto Fear & Greed Index API.
"""
import requests
from typing import Dict, Optional
from datetime import datetime


class FearGreedIndex:
    """Fetch and parse the Crypto Fear & Greed Index."""
    
    def __init__(self):
        """Initialize Fear & Greed Index fetcher."""
        self.api_url = "https://api.alternative.me/fng/"
    
    def get_current_index(self) -> Optional[Dict]:
        """
        Get the current Fear & Greed Index.
        
        Returns:
            Dictionary with index data or None if error:
            {
                'value': int (0-100),
                'classification': str ('Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'),
                'timestamp': str,
                'time_until_update': str
            }
        """
        try:
            response = requests.get(self.api_url, params={'limit': 1}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data or not data['data']:
                return None
            
            index_data = data['data'][0]
            value = int(index_data['value'])
            
            return {
                'value': value,
                'classification': index_data['value_classification'],
                'timestamp': index_data['timestamp'],
                'time_until_update': index_data.get('time_until_update', 'N/A')
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Fear & Greed Index: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing Fear & Greed Index data: {e}")
            return None
    
    def get_historical_index(self, limit: int = 30) -> Optional[list]:
        """
        Get historical Fear & Greed Index data.
        
        Args:
            limit: Number of historical data points (default: 30 days)
        
        Returns:
            List of dictionaries with historical data or None if error
        """
        try:
            response = requests.get(self.api_url, params={'limit': limit}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                return None
            
            historical_data = []
            for entry in data['data']:
                historical_data.append({
                    'value': int(entry['value']),
                    'classification': entry['value_classification'],
                    'timestamp': entry['timestamp']
                })
            
            return historical_data
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical Fear & Greed Index: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing historical data: {e}")
            return None
    
    def get_emoji(self, value: int) -> str:
        """
        Get emoji representation for Fear & Greed value.
        
        Args:
            value: Fear & Greed Index value (0-100)
        
        Returns:
            Emoji string
        """
        if value <= 25:
            return "😱"  # Extreme Fear
        elif value <= 45:
            return "😰"  # Fear
        elif value <= 55:
            return "😐"  # Neutral
        elif value <= 75:
            return "🤑"  # Greed
        else:
            return "🚀"  # Extreme Greed
    
    def should_trade(self, value: int, strategy: str = "contrarian") -> bool:
        """
        Determine if it's a good time to trade based on the index.
        
        Args:
            value: Fear & Greed Index value (0-100)
            strategy: Trading strategy ('contrarian' or 'momentum')
                     - contrarian: Buy when fearful, sell when greedy
                     - momentum: Buy when greedy, sell when fearful
        
        Returns:
            True if conditions favor trading, False otherwise
        """
        if strategy == "contrarian":
            # Buy opportunity when market is fearful (< 40)
            return value < 40
        elif strategy == "momentum":
            # Buy opportunity when market is greedy (> 60)
            return value > 60
        else:
            return False
    
    def format_report(self, index_data: Optional[Dict] = None) -> str:
        """
        Format a human-readable report of the Fear & Greed Index.
        
        Args:
            index_data: Index data dictionary (fetches current if None)
        
        Returns:
            Formatted report string
        """
        if index_data is None:
            index_data = self.get_current_index()
        
        if not index_data:
            return "❌ Unable to fetch Fear & Greed Index"
        
        value = index_data['value']
        classification = index_data['classification']
        emoji = self.get_emoji(value)
        
        report = f"{emoji} Fear & Greed Index: {value}/100\n"
        report += f"   Classification: {classification}\n"
        
        # Add trading suggestion
        if value < 25:
            report += "   💡 Extreme Fear - Potential buying opportunity (contrarian)\n"
        elif value < 40:
            report += "   💡 Fear - Consider accumulating positions\n"
        elif value > 75:
            report += "   ⚠️  Extreme Greed - Consider taking profits\n"
        elif value > 60:
            report += "   ⚠️  Greed - Market heating up, be cautious\n"
        else:
            report += "   😐 Neutral - Market balanced\n"
        
        return report


def main():
    """Test the Fear & Greed Index fetcher."""
    fgi = FearGreedIndex()
    
    print("=" * 60)
    print("CRYPTO FEAR & GREED INDEX")
    print("=" * 60)
    print()
    
    # Get current index
    current = fgi.get_current_index()
    if current:
        print(fgi.format_report(current))
        print()
        
        # Check trading recommendation
        print("Trading Recommendations:")
        print(f"  Contrarian Strategy: {'✅ BUY' if fgi.should_trade(current['value'], 'contrarian') else '❌ WAIT'}")
        print(f"  Momentum Strategy: {'✅ BUY' if fgi.should_trade(current['value'], 'momentum') else '❌ WAIT'}")
    else:
        print("Failed to fetch Fear & Greed Index")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
