"""
Query Tavily for today's most positively talked about cryptocurrencies.
"""
import os
from datetime import datetime
from tavily import TavilyClient
from typing import Dict, List, Optional


class TavilyCryptoQuery:
    """Class for querying Tavily for cryptocurrency news and sentiment."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Tavily crypto query client.
        
        Args:
            api_key: Tavily API key. If None, will read from TAVILY_API environment variable
            
        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        self.api_key = api_key or os.getenv("TAVILY_API")
        if not self.api_key:
            raise ValueError("TAVILY_API environment variable not set or api_key not provided")
        
        self.client = TavilyClient(api_key=self.api_key)
    
    def get_positive_crypto_news(self,
                                 max_results: int = 10,
                                 search_depth: str = "advanced") -> Dict:
        """
        Query Tavily for today's most positively talked about cryptocurrencies.
        
        Args:
            max_results: Maximum number of results to return (default: 10)
            search_depth: Search depth - "basic" or "advanced" (default: advanced)
        
        Returns:
            dict: Search results containing information about positively discussed cryptocurrencies
        """
        # Get today's date for context
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Construct search query for positive crypto sentiment
        query = f"most positively discussed cryptocurrencies today {today} bullish sentiment good news"
        
        # Search with Tavily
        results = self.client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_domains=[],  # Can specify crypto news sites if needed
            exclude_domains=[],
            include_answer=True,  # Get AI-generated answer summary
            include_raw_content=False,
        )
        
        return results
    
    def extract_crypto_symbols(self, results: Dict) -> List[str]:
        """
        Extract cryptocurrency symbols mentioned in the results.
        
        Args:
            results: Tavily search results
            
        Returns:
            List of cryptocurrency symbols found
        """
        symbols = []
        common_cryptos = {
            'bitcoin': 'BTC', 'btc': 'BTC',
            'ethereum': 'ETH', 'eth': 'ETH',
            'ripple': 'XRP', 'xrp': 'XRP',
            'cardano': 'ADA', 'ada': 'ADA',
            'solana': 'SOL', 'sol': 'SOL',
            'polkadot': 'DOT', 'dot': 'DOT',
            'avalanche': 'AVAX', 'avax': 'AVAX',
            'chainlink': 'LINK', 'link': 'LINK',
            'polygon': 'MATIC', 'matic': 'MATIC',
            'binance': 'BNB', 'bnb': 'BNB',
        }
        
        text = ""
        if results.get("answer"):
            text += results["answer"].lower() + " "
        
        if results.get("results"):
            for result in results["results"]:
                if result.get("title"):
                    text += result["title"].lower() + " "
                if result.get("content"):
                    text += result["content"].lower() + " "
        
        # Extract symbols
        for name, symbol in common_cryptos.items():
            if name in text and symbol not in symbols:
                symbols.append(symbol)
        
        return symbols
    
    def print_results(self, results: Dict, verbose: bool = True):
        """
        Pretty print the Tavily search results.
        
        Args:
            results: Results from Tavily search
            verbose: Whether to print detailed results (default: True)
        """
        if not verbose:
            return
        
        print("\n" + "="*80)
        print("TODAY'S MOST POSITIVELY TALKED ABOUT CRYPTOCURRENCIES")
        print("="*80 + "\n")
        
        # Print AI-generated answer if available
        if results.get("answer"):
            print("SUMMARY:")
            print("-" * 80)
            print(results["answer"])
            print("\n")
        
        # Print individual results
        if results.get("results"):
            print("DETAILED RESULTS:")
            print("-" * 80)
            for idx, result in enumerate(results["results"], 1):
                print(f"\n{idx}. {result.get('title', 'No title')}")
                print(f"   URL: {result.get('url', 'No URL')}")
                print(f"   Score: {result.get('score', 0):.3f}")
                if result.get("content"):
                    # Truncate content for readability
                    content = result["content"]
                    if len(content) > 300:
                        content = content[:300] + "..."
                    print(f"   Content: {content}")
                print()
        
        print("="*80)
    
    def analyze_crypto_sentiment(self, crypto_symbol: str, crypto_name: str = "") -> Dict:
        """
        Analyze sentiment for a specific cryptocurrency.
        
        Args:
            crypto_symbol: Symbol like "BINANCE:BTCUSDT" or "BTC"
            crypto_name: Name of the cryptocurrency
            
        Returns:
            Dictionary with sentiment analysis and reasoning
        """
        # Clean up the symbol to just get the crypto part
        clean_symbol = crypto_symbol.split(':')[-1].replace('USDT', '').replace('USD', '')
        
        # Build more specific query for this crypto
        today = datetime.now().strftime("%Y-%m-%d")
        # Add "crypto" and "token" keywords to avoid confusion with other topics
        query = f"{clean_symbol} cryptocurrency token news sentiment {today}"
        if crypto_name:
            query = f"{clean_symbol} {crypto_name} crypto token news sentiment {today}"
        
        try:
            results = self.client.search(
                query=query,
                search_depth="basic",
                max_results=5,
                include_answer=True,
                include_raw_content=False,
            )
            
            # Extract reasoning from AI answer
            reasoning = results.get('answer', 'No additional context available.')
            
            # Validate that the reasoning is actually about the crypto
            # Check if the crypto symbol or common crypto terms appear
            crypto_terms = ['crypto', 'token', 'blockchain', 'coin', 'price', 'trading', 'exchange']
            reasoning_lower = reasoning.lower()
            
            # If reasoning doesn't seem crypto-related, mark as unknown
            if clean_symbol.lower() not in reasoning_lower and not any(term in reasoning_lower for term in crypto_terms):
                sentiment = 'unknown'
                reasoning = f"No relevant news found for {clean_symbol}. This may be a newly listed or obscure token."
            else:
                # Analyze sentiment from the results
                sentiment = self._analyze_sentiment_from_text(results)
                
                # Truncate reasoning if too long
                if len(reasoning) > 300:
                    reasoning = reasoning[:297] + "..."
            
            return {
                'symbol': crypto_symbol,
                'clean_symbol': clean_symbol,
                'name': crypto_name,
                'sentiment': sentiment,
                'reasoning': reasoning,
                'results': results
            }
        except Exception as e:
            print(f"Error analyzing {clean_symbol}: {e}")
            return {
                'symbol': crypto_symbol,
                'clean_symbol': clean_symbol,
                'name': crypto_name,
                'sentiment': 'unknown',
                'reasoning': f"Failed to analyze: {str(e)}",
                'results': None
            }
    
    def _analyze_sentiment_from_text(self, results: Dict) -> str:
        """
        Analyze sentiment from Tavily results.
        
        Returns: 'fearful', 'excitement', 'doubt', 'hype', or 'neutral'
        """
        text = ""
        if results.get("answer"):
            text += results["answer"].lower() + " "
        
        if results.get("results"):
            for result in results["results"]:
                if result.get("content"):
                    text += result["content"].lower() + " "
        
        # Sentiment keywords
        fearful_words = ['crash', 'dump', 'fear', 'panic', 'loss', 'decline', 'drop', 'falling', 'bearish', 'sell-off']
        excitement_words = ['bullish', 'surge', 'rally', 'pump', 'moon', 'breakout', 'all-time high', 'ath', 'soaring']
        doubt_words = ['uncertain', 'skeptical', 'concern', 'worry', 'cautious', 'hesitant', 'risky', 'volatile']
        hype_words = ['hype', 'fomo', 'trending', 'viral', 'explosive', 'massive', 'huge potential', 'next big']
        
        # Count occurrences
        scores = {
            'fearful': sum(1 for word in fearful_words if word in text),
            'excitement': sum(1 for word in excitement_words if word in text),
            'doubt': sum(1 for word in doubt_words if word in text),
            'hype': sum(1 for word in hype_words if word in text)
        }
        
        # Determine dominant sentiment
        if max(scores.values()) == 0:
            return 'neutral'
        
        return max(scores, key=scores.get)
    
    def analyze_multiple_cryptos(self, crypto_list: List[Dict], verbose: bool = True) -> List[Dict]:
        """
        Analyze sentiment for multiple cryptocurrencies.
        
        Args:
            crypto_list: List of crypto dicts with 'symbol' and 'name' keys
            verbose: Whether to print progress
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        
        for crypto in crypto_list:
            if verbose:
                print(f"Analyzing sentiment for {crypto.get('symbol', 'Unknown')}...")
            
            sentiment_result = self.analyze_crypto_sentiment(
                crypto.get('symbol', ''),
                crypto.get('name', '')
            )
            results.append(sentiment_result)
        
        return results
    
    def search(self, verbose: bool = True) -> Dict:
        """
        Main method to search for positive crypto news.
        
        Args:
            verbose: Whether to print results (default: True)
            
        Returns:
            Dictionary with search results
        """
        if verbose:
            today = datetime.now().strftime("%Y-%m-%d")
            query = f"most positively discussed cryptocurrencies today {today} bullish sentiment good news"
            print(f"Searching for: {query}")
        
        results = self.get_positive_crypto_news()
        
        if verbose:
            self.print_results(results, verbose=True)
            
            # Extract and show mentioned symbols
            symbols = self.extract_crypto_symbols(results)
            if symbols:
                print(f"\n💡 Cryptocurrencies mentioned: {', '.join(symbols)}")
                print("="*80)
        
        return results


def main():
    """Main entry point for the crypto query script standalone usage."""
    try:
        query = TavilyCryptoQuery()
        results = query.search(verbose=True)
        return results
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set the TAVILY_API environment variable:")
        print("export TAVILY_API='your_api_key_here'")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    main()
