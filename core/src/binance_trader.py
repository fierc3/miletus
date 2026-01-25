"""
Binance trading automation with Take Profit and Stop Loss functionality.
"""
import os
from typing import Dict, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time


class BinanceTrader:
    """Handles automated trading on Binance with TP/SL orders."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        """
        Initialize Binance trader.
        
        Args:
            api_key: Binance API key (defaults to BINANCE_API_KEY env var)
            api_secret: Binance API secret (defaults to BINANCE_API_SECRET env var)
            testnet: Use testnet for testing (defaults to False)
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API credentials not provided. Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")
        
        self.testnet = testnet
        if testnet:
            self.client = Client(self.api_key, self.api_secret, testnet=True)
        else:
            self.client = Client(self.api_key, self.api_secret)
        
        # Track active positions
        self.active_positions = {}
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            Current price as float
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Error getting price for {symbol}: {e}")
            raise
    
    def get_account_balance(self, asset: str = "USDT") -> float:
        """
        Get account balance for a specific asset.
        
        Args:
            asset: Asset symbol (default: "USDT")
            
        Returns:
            Available balance as float
        """
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except BinanceAPIException as e:
            print(f"Error getting balance for {asset}: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get trading pair information including filters.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            Dictionary with symbol information, or None if symbol not found
        """
        try:
            info = self.client.get_symbol_info(symbol)
            
            if not info:
                return None
            
            # Extract relevant filters
            filters = {}
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    filters['min_qty'] = float(f['minQty'])
                    filters['max_qty'] = float(f['maxQty'])
                    filters['step_size'] = float(f['stepSize'])
                elif f['filterType'] == 'PRICE_FILTER':
                    filters['min_price'] = float(f['minPrice'])
                    filters['max_price'] = float(f['maxPrice'])
                    filters['tick_size'] = float(f['tickSize'])
                elif f['filterType'] == 'MIN_NOTIONAL':
                    filters['min_notional'] = float(f['minNotional'])
            
            return {
                'symbol': info['symbol'],
                'status': info['status'],
                'base_asset': info['baseAsset'],
                'quote_asset': info['quoteAsset'],
                'filters': filters
            }
        except BinanceAPIException as e:
            print(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def round_step_size(self, quantity: float, step_size: float) -> float:
        """
        Round quantity to match step size requirements.
        
        Args:
            quantity: Original quantity
            step_size: Step size from symbol filters
            
        Returns:
            Rounded quantity
        """
        precision = len(str(step_size).split('.')[-1].rstrip('0'))
        return round(quantity - (quantity % step_size), precision)
    
    def is_already_invested(self, symbol: str) -> bool:
        """
        Check if already invested in a symbol.
        Assumes symbol has already been validated to exist.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            True if already invested, False otherwise
        """
        # Check active positions tracker
        if symbol in self.active_positions:
            print(f"   ℹ️  Found {symbol} in active_positions tracker")
            return True
        
        # Check actual account balance
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return False  # Symbol doesn't exist, so not invested
            
            base_asset = symbol_info['base_asset']
            
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == base_asset:
                    balance_amount = float(balance['free']) + float(balance['locked'])
                    
                    # Only consider it "invested" if the position is worth at least $10
                    # This avoids false positives from dust amounts
                    if balance_amount > 0:
                        current_price = self.get_current_price(symbol)
                        position_value_usd = balance_amount * current_price
                        
                        print(f"   ℹ️  {base_asset} balance: {balance_amount:.8f} (${position_value_usd:.2f})")
                        
                        if position_value_usd >= 10.0:  # Minimum $10 position
                            print(f"   ℹ️  Position value ${position_value_usd:.2f} >= $10 threshold")
                            return True
            return False
        except Exception as e:
            print(f"   ⚠️  Error checking investment status for {symbol}: {e}")
            return True  # Be cautious and assume invested if error
    
    def calculate_tp_sl_prices(self, entry_price: float, 
                                tp_percent_min: float = 5.0, 
                                tp_percent_max: float = 15.0,
                                sl_percent_min: float = 2.0,
                                sl_percent_max: float = 5.0) -> Tuple[float, float]:
        """
        Calculate Take Profit and Stop Loss prices based on entry price.
        Uses the midpoint of the specified ranges.
        
        Args:
            entry_price: Entry price for the trade
            tp_percent_min: Minimum TP percentage (default: 5%)
            tp_percent_max: Maximum TP percentage (default: 15%)
            sl_percent_min: Minimum SL percentage (default: 2%)
            sl_percent_max: Maximum SL percentage (default: 5%)
            
        Returns:
            Tuple of (take_profit_price, stop_loss_price)
        """
        # Use midpoint of ranges
        tp_percent = (tp_percent_min + tp_percent_max) / 2
        sl_percent = (sl_percent_min + sl_percent_max) / 2
        
        take_profit_price = entry_price * (1 + tp_percent / 100)
        stop_loss_price = entry_price * (1 - sl_percent / 100)
        
        return take_profit_price, stop_loss_price
    
    def place_market_buy_with_tp_sl(self, symbol: str,
                                      usdt_amount: float = 100.0,
                                      tp_percent_min: float = 5.0,
                                      tp_percent_max: float = 15.0,
                                      sl_percent_min: float = 2.0,
                                      sl_percent_max: float = 5.0) -> Dict:
        """
        Place a market buy order with OCO (One-Cancels-Other) for TP and SL.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            usdt_amount: Amount in USDT to invest (default: 100)
            tp_percent_min: Minimum TP percentage (default: 5%)
            tp_percent_max: Maximum TP percentage (default: 15%)
            sl_percent_min: Minimum SL percentage (default: 2%)
            sl_percent_max: Maximum SL percentage (default: 5%)
            
        Returns:
            Dictionary with order results
        """
        try:
            # Get symbol info first to validate it exists
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'Symbol {symbol} not available on Binance',
                    'orders': []
                }
            
            # Check if already invested
            if self.is_already_invested(symbol):
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'Already invested in {symbol}',
                    'orders': []
                }
            
            # Get current price
            current_price = self.get_current_price(symbol)
            
            # Calculate quantity to buy
            quantity = usdt_amount / current_price
            quantity = self.round_step_size(quantity, symbol_info['filters']['step_size'])
            
            # Validate quantity meets minimum
            if quantity < symbol_info['filters']['min_qty']:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'Quantity {quantity} below minimum {symbol_info["filters"]["min_qty"]}',
                    'orders': []
                }
            
            # Check account balance
            balance = self.get_account_balance('USDT')
            if balance < usdt_amount:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'Insufficient balance. Have {balance} USDT, need {usdt_amount} USDT',
                    'orders': []
                }
            
            # Place market buy order
            print(f"Placing market buy order for {quantity} {symbol} at ~${current_price:.8f}...")
            buy_order = self.client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            buy_order_id = buy_order['orderId']  # Save for error reporting
            
            # Wait for order to fill and get actual fill price
            time.sleep(2)
            order_status = self.client.get_order(symbol=symbol, orderId=buy_order_id)
            
            # Calculate actual entry price from fills
            entry_price = current_price
            actual_quantity = quantity  # Default to expected quantity
            if order_status['status'] == 'FILLED' and 'fills' in order_status:
                total_cost = sum(float(fill['price']) * float(fill['qty']) for fill in order_status['fills'])
                total_qty = sum(float(fill['qty']) for fill in order_status['fills'])
                entry_price = total_cost / total_qty if total_qty > 0 else current_price
                actual_quantity = total_qty  # Use actual filled quantity
            
            print(f"✅ Buy order filled at ${entry_price:.8f}")
            
            # Calculate TP and SL prices
            tp_price, sl_price = self.calculate_tp_sl_prices(
                entry_price, tp_percent_min, tp_percent_max, sl_percent_min, sl_percent_max
            )
            
            # Round prices to tick size
            tick_size = symbol_info['filters']['tick_size']
            tp_price = self.round_step_size(tp_price, tick_size)
            sl_price = self.round_step_size(sl_price, tick_size)
            
            # Round actual quantity to step size for OCO order
            actual_quantity = self.round_step_size(actual_quantity, symbol_info['filters']['step_size'])
            
            print(f"Setting TP at ${tp_price:.8f} (+{((tp_price/entry_price - 1) * 100):.2f}%)")
            print(f"Setting SL at ${sl_price:.8f} ({((sl_price/entry_price - 1) * 100):.2f}%)")
            
            # Place OCO order using new Binance API format
            # OCO = One-Cancels-Other: when TP hits, SL cancels (and vice versa)
            oco_params = {
                'symbol': symbol,
                'side': 'SELL',
                'quantity': actual_quantity,  # Use actual filled quantity
                'aboveType': 'LIMIT_MAKER',
                'abovePrice': f"{tp_price:.8f}",
                'belowType': 'STOP_LOSS_LIMIT',
                'belowPrice': f"{sl_price:.8f}",
                'belowStopPrice': f"{sl_price:.8f}",
                'belowTimeInForce': 'GTC'
            }
            
            # Use signed request directly for new OCO format
            try:
                oco_order = self.client._request_api(
                    'post',
                    'orderList/oco',
                    signed=True,
                    data=oco_params
                )
                print(f"✅ OCO order placed (TP: ${tp_price:.8f}, SL: ${sl_price:.8f})")
            except Exception as oco_error:
                # OCO failed but buy succeeded - critical error!
                print(f"🚨 CRITICAL: Buy order filled but OCO placement failed!")
                print(f"   Symbol: {symbol}")
                print(f"   Entry: ${entry_price:.8f}")
                print(f"   Quantity: {actual_quantity}")
                print(f"   Buy Order ID: {buy_order_id}")
                print(f"   OCO Error: {oco_error}")
                print(f"   ⚠️  POSITION IS UNPROTECTED - Manual intervention required!")
                
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'Buy succeeded but OCO failed: {oco_error}',
                    'partial_fill': True,  # Flag that buy succeeded
                    'buy_order_id': buy_order_id,
                    'entry_price': entry_price,
                    'quantity': actual_quantity,
                    'orders': []
                }
            
            # Track position
            self.active_positions[symbol] = {
                'entry_price': entry_price,
                'quantity': actual_quantity,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'buy_order_id': buy_order['orderId'],
                'oco_order_id': oco_order.get('orderListId', 'unknown')
            }
            
            return {
                'success': True,
                'symbol': symbol,
                'message': 'Trade executed successfully',
                'entry_price': entry_price,
                'quantity': actual_quantity,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'tp_percent': ((tp_price/entry_price - 1) * 100),
                'sl_percent': ((sl_price/entry_price - 1) * 100),
                'orders': {
                    'buy_order': buy_order,
                    'oco_order': oco_order
                }
            }
            
        except BinanceAPIException as e:
            return {
                'success': False,
                'symbol': symbol,
                'message': f'Binance API error: {e}',
                'orders': []
            }
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol,
                'message': f'Error: {e}',
                'orders': []
            }
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all open orders.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of open orders
        """
        try:
            if symbol:
                return self.client.get_open_orders(symbol=symbol)
            else:
                return self.client.get_open_orders()
        except BinanceAPIException as e:
            print(f"Error getting open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancel a specific order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            return True
        except BinanceAPIException as e:
            print(f"Error canceling order {order_id}: {e}")
            return False


def main():
    """Example usage of BinanceTrader."""
    # Initialize trader (set testnet=True for testing)
    trader = BinanceTrader(testnet=False)
    
    print("=" * 100)
    print("BINANCE TRADER - TP/SL AUTOMATION")
    print("=" * 100)
    
    # Example: Place a trade on BTCUSDT
    symbol = "BTCUSDT"
    usdt_amount = 100.0  # Invest $100
    
    result = trader.place_market_buy_with_tp_sl(
        symbol=symbol,
        usdt_amount=usdt_amount,
        tp_percent_min=5.0,   # TP: +5% to +15%
        tp_percent_max=15.0,
        sl_percent_min=2.0,   # SL: -2% to -5%
        sl_percent_max=5.0
    )
    
    if result['success']:
        print(f"\n✅ Trade executed successfully!")
        print(f"Symbol: {result['symbol']}")
        print(f"Entry Price: ${result['entry_price']:.8f}")
        print(f"Quantity: {result['quantity']}")
        print(f"Take Profit: ${result['tp_price']:.8f} (+{result['tp_percent']:.2f}%)")
        print(f"Stop Loss: ${result['sl_price']:.8f} ({result['sl_percent']:.2f}%)")
    else:
        print(f"\n❌ Trade failed: {result['message']}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
