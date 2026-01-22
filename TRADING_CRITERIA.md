# Trading Criteria

Miletus uses a multi-layered filtering system to identify high-quality cryptocurrency trading opportunities. A trade is only executed when **all** of the following criteria are met:

---

## 🔍 Step 1: TradingView Technical Analysis

The system scans Binance for cryptocurrencies that meet these technical requirements:

### Volume Requirements
- **Minimum Volume**: $500,000 USD (24h)
- **Volume Change Range**: 0% to 500% vs 10-day average
  - Ensures sufficient liquidity
  - Filters out manipulation (>500% volume spikes)

### Technical Rating
Must have one of these ratings from TradingView:
- ✅ **STRONG_BUY** (>= 0.5 score)
- ✅ **BUY** (>= 0.1 score)
- ✅ **NEUTRAL** (between -0.1 and 0.1)

❌ **Excluded**: SELL and STRONG_SELL ratings

### Additional Filters
- Listed on **Binance** exchange
- Trading pair ends in **USDT**
- Excludes stablecoin pairs (USDC, BUSD, DAI)
- Excludes leveraged tokens (UP/DOWN)

---

## 🧠 Step 2: AI Sentiment Analysis

The top 10 technical candidates undergo sentiment analysis using Tavily AI:

### Sentiment Categories
Only these sentiments are allowed for trading:
- ✅ **Excitement** 🚀 - Strong positive momentum
- ✅ **Hype** 🔥 - Building market interest
- ✅ **Neutral** 😐 - Balanced, no negative news

❌ **Excluded Sentiments**:
- ❌ **Fearful** 😨 - Market concerns
- ❌ **Doubt** 🤔 - Uncertainty or skepticism

### Analysis Sources
- Recent news articles
- Social media sentiment
- Market developments
- Expert opinions

---

## 📊 Step 3: Market Conditions (Fear & Greed Index)

Before executing any trades, the system checks overall market sentiment:

### Fear & Greed Scale (0-100)
- **0-25**: Extreme Fear 😱 - ✅ Trading allowed
- **25-45**: Fear 😰 - ✅ Trading allowed
- **45-55**: Neutral 😐 - ✅ Trading allowed
- **55-75**: Greed 🤑 - ✅ Trading allowed
- **75-100**: Extreme Greed 🚀 - ❌ **ALL TRADING BLOCKED**

**Rationale**: Extreme Greed (>75) indicates an overheated market prone to corrections. The system protects capital by avoiding entries during these periods.

---

## 💰 Step 4: Position Management

Before placing a trade, the system verifies:

### Existing Positions
- ❌ **Skips** if already holding the asset (position worth ≥ $10)
- Prevents over-concentration in a single cryptocurrency

### Balance Verification
- Confirms sufficient USDT balance
- Validates quantity meets Binance minimum requirements
- Checks price precision and step size compliance

---

## 🎯 Trade Execution Parameters

When all criteria are met, the system executes with these settings:

### Position Sizing
- **Default**: $100 USDT per trade
- **Configurable** via `BINANCE_TRADE_AMOUNT_USDT` environment variable

### Risk Management
- **Take Profit**: +5% to +15% (randomized for each trade)
- **Stop Loss**: -2% to -5% (randomized for each trade)
- **Order Type**: OCO (One-Cancels-Other)
  - When TP hits, SL automatically cancels
  - When SL hits, TP automatically cancels

### Symbol Validation
- Verifies symbol exists on Binance
- Checks symbol is currently tradable
- Ensures sufficient market liquidity

---

## 📝 Summary: Complete Trade Checklist

A cryptocurrency must pass **ALL** of these checks:

- [x] Volume > $500K (24h)
- [x] Volume change 0-500% vs 10-day average
- [x] Technical rating: BUY, STRONG_BUY, or NEUTRAL
- [x] AI sentiment: Excitement, Hype, or Neutral
- [x] Fear & Greed Index ≤ 75
- [x] No existing position in the asset
- [x] Sufficient USDT balance
- [x] Symbol tradable on Binance
- [x] Meets Binance minimum quantity requirements

---

## ⚙️ Configuration Options

Customize trading behavior via environment variables:

```bash
# Trading Control
BINANCE_TRADING_ENABLED=true
BINANCE_USE_TESTNET=false

# Position Sizing
BINANCE_TRADE_AMOUNT_USDT=100

# Risk Management
BINANCE_TP_MIN=5      # Minimum take profit %
BINANCE_TP_MAX=15     # Maximum take profit %
BINANCE_SL_MIN=2      # Minimum stop loss %
BINANCE_SL_MAX=5      # Maximum stop loss %
```

---

## 🛡️ Safety Features

- **Testnet Mode**: Practice with fake money before going live
- **API Key Validation**: Verifies credentials before trading
- **Balance Checks**: Prevents trades exceeding available funds
- **Duplicate Prevention**: Won't double-buy existing positions
- **Market Condition Gates**: Blocks trading during extreme conditions
- **Detailed Logging**: Every decision is explained in console output
- **Telegram Notifications**: Real-time alerts for executed trades

---

**Last Updated**: January 2026
