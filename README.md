# Miletus


**Miletus** is an AI-powered cryptocurrency trading analysis platform that identifies high-potential investment opportunities through multi-layered technical and sentiment analysis. The system automatically scans TradingView for cryptocurrencies with strong technical indicators (STRONG_BUY/BUY ratings, optimal RSI levels, healthy volume patterns), then enriches the top candidates with real-time sentiment analysis powered by Tavily AI to classify market mood as excitement, fear, doubt, or hype. Results are intelligently filtered to exclude manipulation risks, sorted by technical strength, and delivered via Telegram with actionable insights including price movements, volume metrics, and AI-generated reasoning. Designed for automated hourly execution via GitHub Actions, Miletus combines quantitative technical analysis with qualitative news sentiment to help traders make informed decisions in the volatile crypto market.

## Key Features

- 📊 **TradingView Integration** - Real-time technical analysis with RSI, volume, and rating indicators
- 🤖 **AI Sentiment Analysis** - Tavily-powered news sentiment classification (excitement, fear, doubt, hype)
- 🔔 **Telegram Alerts** - Automated notifications with detailed crypto insights
- ⏰ **Automated Execution** - Hourly GitHub Actions workflow for continuous monitoring
- 🛡️ **Manipulation Detection** - Filters out suspicious volume spikes (>500%)
- 🎯 **Smart Prioritization** - STRONG_BUY signals ranked first with volume-based sorting
- 💎 **Quality Filtering** - USDT pairs only, excludes low-quality DEX tokens


```text
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
     @@      @@    .@ @  =@@@@@@@@* @ @+    @@      @@     
      @@      @     @@                @@     @      @@      
       @@@    @@      @@  @      @  @@      @@    @@@       
         @@    @@       @@@@    @@@@       @@    @@         
          @@@    @@         @@@@         @@    @@@          
            @@@   @@@                  @@@   @@@            
               @@@   @@@            @@@   @@@               
                 @@@@    @@@@@@@@@@    @@@@                 
                     @@@@@@@@  @@@@@@@@                     
```
