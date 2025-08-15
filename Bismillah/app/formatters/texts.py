
def format_analyze(data):
    """Format analyze command output with professional styling"""
    return f"""🔍 **PROFESSIONAL COMPREHENSIVE ANALYSIS - {data['coin']}**

💰 **Current Price**: ${data['price']:.6f}
📊 **24h Change**: Analysis in progress
📈 **Trend**: {data['trend'].title()}

```
💰 TECHNICAL INDICATORS:
• RSI(14): {data['rsi']:.1f}
• MACD Histogram: {data['macd_hist']:.6f}
• ATR(14): ${data['atr']:.6f}
• Trend Strength: {data['trend'].title()}
```

🎯 **SINGLE ENTRY POINT STRATEGY**:
• **Entry**: ${data['entry_one']:.6f}

💡 **ADVANCED TRADING INSIGHTS**:
• Single entry point eliminates confusion
• Entry calculated using EMA50 + ATR optimization
• Risk management built into entry logic

⚠️ **RISK MANAGEMENT PROTOCOL**:
• Gunakan proper position sizing (1-3% per trade)
• Set stop loss sebelum entry
• Monitor volume for confirmation
• DYOR sebelum trading

📡 **Data Sources**: CoinAPI Real-time + Enhanced Analysis
🔄 **Update Frequency**: Real-time price + Technical refresh"""

def format_futures(data):
    """Format futures command output"""
    return f"""🔍 **PROFESSIONAL FUTURES ANALYSIS - {data['coin']}**

💰 **Current Price**: ${data['price']:.6f}
🎯 **Single Entry Point**: ${data['entry']:.6f}
📈 **Trend Direction**: {data['trend'].title()}

```
💰 SINGLE ENTRY STRATEGY:
• Entry Point: ${data['entry']:.6f}
• Strategy: Single point execution
• Risk Level: Optimized
```

💡 **ENTRY POINT LOGIC**:
• Calculated using EMA50 + ATR methodology
• Eliminates multiple entry confusion
• Risk-optimized positioning

⚠️ **TRADING RULES**:
• Use single entry point only
• Proper position sizing (1-3% risk)
• Set stop loss before entry
• Monitor volume for confirmation

📡 **Data Source**: CoinAPI Real-time
🔄 **Analysis**: Professional single-entry strategy"""

def format_futures_signals(signals_list):
    """Format futures signals output"""
    text = f"""🚨 **FUTURES SIGNALS – SINGLE ENTRY ANALYSIS**

🕐 **Scan Time**: Live Analysis
📊 **Signals Found**: {len([s for s in signals_list if s.get('ok', False)])} Good Signals

"""
    
    count = 1
    for signal in signals_list:
        if "error" in signal:
            text += f"{count}. ❌ **{signal['coin']}** - Data Error\n\n"
        else:
            status_emoji = "🟢" if signal['ok'] else "🔴"
            status_text = "GOOD SIGNAL" if signal['ok'] else "WAIT"
            
            text += f"""{count}. {signal['coin']} {status_emoji} **{status_text}**
💰 **Entry**: ${signal['entry']:.6f}
📊 **RSI**: {signal['rsi']:.1f}
📈 **MACD**: {signal['macd_hist']:.6f}
🔄 **Trend**: {signal['trend'].title()}
📈 **Current Price**: ${signal['price']:.6f}

"""
        count += 1
    
    text += """⚠️ **TRADING DISCLAIMER**:
• Signals based on single entry point strategy
• Use proper risk management
• Position sizing according to risk level
• DYOR before trading

📡 **Data Source**: CoinAPI Real-time Analysis"""
    
    return text

def format_market(market_data):
    """Format market overview output"""
    text = """🌍 **COMPREHENSIVE MARKET ANALYSIS**

🕐 **Analysis Time**: Live Data
📊 **Market Overview**: CoinAPI Real-time

"""
    
    count = 1
    for coin, data in market_data['coins'].items():
        if "error" in data:
            text += f"{count}. ❌ **{coin}** - Data Error\n"
        else:
            text += f"{count}. 💰 **{coin}**: ${data['price']:.6f}\n"
        count += 1
    
    text += """
📊 **Market Status**: Real-time pricing active
📡 **Data Source**: CoinAPI Professional
🔄 **Update**: Live market data

💡 **Market Insights**:
• Real-time price feeds active
• Professional-grade data source
• Suitable for trading decisions"""
    
    return text
