"""
Liquidate all positions and cancel all open orders on Binance testnet.
This script sells all crypto holdings and converts them back to USDT.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from binance_trader import BinanceTrader

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def liquidate_specific_symbol(symbol: str):
    """
    Liquidate a specific symbol and cancel its open orders.
    
    Args:
        symbol: Trading pair symbol (e.g., "RPLUSDT")
    """
    print("=" * 80)
    print(f"LIQUIDATING {symbol}")
    print("=" * 80)
    print()
    
    try:
        trader = BinanceTrader(testnet=True)
        
        # Step 1: Cancel open orders for this symbol
        print(f"Step 1: Canceling open orders for {symbol}...")
        print("-" * 80)
        
        open_orders = trader.client.get_open_orders(symbol=symbol)
        if open_orders:
            print(f"Found {len(open_orders)} open orders")
            for order in open_orders:
                order_id = order['orderId']
                try:
                    trader.client.cancel_order(symbol=symbol, orderId=order_id)
                    print(f"✅ Canceled order {order_id}")
                except Exception as e:
                    print(f"⚠️  Failed to cancel order {order_id}: {e}")
        else:
            print("No open orders to cancel")
        
        print()
        
        # Step 2: Sell the position
        print(f"Step 2: Selling {symbol} position...")
        print("-" * 80)
        
        # Get symbol info
        symbol_info = trader.get_symbol_info(symbol)
        if not symbol_info:
            print(f"❌ {symbol} not available on Binance")
            return
        
        base_asset = symbol_info['base_asset']
        
        # Get balance
        account = trader.client.get_account()
        balance_amount = 0
        
        for balance in account['balances']:
            if balance['asset'] == base_asset:
                balance_amount = float(balance['free']) + float(balance['locked'])
                break
        
        if balance_amount == 0:
            print(f"No {base_asset} balance to sell")
            print("=" * 80)
            return
        
        print(f"Found {balance_amount} {base_asset}")
        
        # Round quantity to step size
        quantity = trader.round_step_size(balance_amount, symbol_info['filters']['step_size'])
        
        # Check minimum quantity
        if quantity < symbol_info['filters']['min_qty']:
            print(f"⚠️  Quantity {quantity} below minimum - dust amount, cannot sell")
            print("=" * 80)
            return
        
        # Get current price for display
        current_price = trader.get_current_price(symbol)
        estimated_usdt = quantity * current_price
        
        print(f"🔄 Selling {quantity} {base_asset} (~${estimated_usdt:.2f})...")
        
        # Place market sell order
        order = trader.client.order_market_sell(
            symbol=symbol,
            quantity=quantity
        )
        
        print(f"✅ Sold {base_asset} successfully - Order ID: {order['orderId']}")
        print(f"💰 Received approximately ${estimated_usdt:.2f} USDT")
        print("=" * 80)
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Make sure BINANCE_API_KEY and BINANCE_API_SECRET are set")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def liquidate_all_positions():
    """
    Liquidate all positions and cancel all open orders.
    """
    print("=" * 80)
    print("LIQUIDATING ALL POSITIONS")
    print("=" * 80)
    print()
    
    try:
        # Initialize trader (testnet=True)
        trader = BinanceTrader(testnet=True)
        
        # Step 1: Cancel all open orders
        print("Step 1: Canceling all open orders...")
        print("-" * 80)
        
        open_orders = trader.client.get_open_orders()
        if open_orders:
            print(f"Found {len(open_orders)} open orders")
            for order in open_orders:
                symbol = order['symbol']
                order_id = order['orderId']
                try:
                    trader.client.cancel_order(symbol=symbol, orderId=order_id)
                    print(f"✅ Canceled order {order_id} for {symbol}")
                except Exception as e:
                    print(f"⚠️  Failed to cancel order {order_id}: {e}")
        else:
            print("No open orders to cancel")
        
        print()
        
        # Step 2: Get all balances
        print("Step 2: Checking account balances...")
        print("-" * 80)
        
        account = trader.client.get_account()
        balances_to_sell = []
        
        for balance in account['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            # Skip USDT and assets with zero balance
            if asset == 'USDT' or total == 0:
                continue
            
            balances_to_sell.append({
                'asset': asset,
                'amount': total
            })
        
        if not balances_to_sell:
            print("No positions to liquidate - account is clean!")
            print()
            print("=" * 80)
            return
        
        print(f"Found {len(balances_to_sell)} positions to liquidate:")
        for bal in balances_to_sell:
            print(f"  • {bal['asset']}: {bal['amount']}")
        
        print()
        
        # Step 3: Sell all positions
        print("Step 3: Selling all positions...")
        print("-" * 80)
        
        successful_sales = 0
        failed_sales = 0
        
        for bal in balances_to_sell:
            asset = bal['asset']
            amount = bal['amount']
            symbol = f"{asset}USDT"
            
            try:
                # Get symbol info to validate and get filters
                symbol_info = trader.get_symbol_info(symbol)
                
                if not symbol_info:
                    print(f"⚠️  {symbol} not tradable on Binance - skipping")
                    failed_sales += 1
                    continue
                
                # Round quantity to step size
                quantity = trader.round_step_size(amount, symbol_info['filters']['step_size'])
                
                # Check minimum quantity
                if quantity < symbol_info['filters']['min_qty']:
                    print(f"⚠️  {asset} quantity {quantity} below minimum - dust amount, skipping")
                    failed_sales += 1
                    continue
                
                # Get current price for display
                current_price = trader.get_current_price(symbol)
                estimated_usdt = quantity * current_price
                
                print(f"🔄 Selling {quantity} {asset} (~${estimated_usdt:.2f})...")
                
                # Place market sell order
                order = trader.client.order_market_sell(
                    symbol=symbol,
                    quantity=quantity
                )
                
                print(f"✅ Sold {asset} successfully - Order ID: {order['orderId']}")
                successful_sales += 1
                
            except Exception as e:
                print(f"❌ Failed to sell {asset}: {e}")
                failed_sales += 1
        
        print()
        print("=" * 80)
        print("LIQUIDATION SUMMARY")
        print("=" * 80)
        print(f"✅ Successfully sold: {successful_sales}")
        print(f"❌ Failed to sell: {failed_sales}")
        print()
        
        # Show final USDT balance
        account = trader.client.get_account()
        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free']) + float(balance['locked'])
                print(f"💰 Final USDT Balance: ${usdt_balance:.2f}")
                break
        
        print("=" * 80)
        print("Account reset complete!")
        print("=" * 80)
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Make sure BINANCE_API_KEY and BINANCE_API_SECRET are set")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    # Check if a specific symbol was provided
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        liquidate_specific_symbol(symbol)
    else:
        liquidate_all_positions()
