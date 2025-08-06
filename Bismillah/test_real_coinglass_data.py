
#!/usr/bin/env python3
"""
Test script untuk memverifikasi bahwa CoinGlass V4 API memberikan data real
dan bukan dummy data seperti $70,000 untuk BTC.
"""

import os
import sys
from datetime import datetime

# Tambahkan path untuk import module
sys.path.append('/home/runner/CryptoMentor-AI-Bot-2025/Bismillah')

from coinglass_provider import CoinGlassProvider
from crypto_api import CryptoAPI

def test_real_data():
    """Test apakah data yang diterima adalah real atau dummy"""
    print("🧪 Testing CoinGlass V4 Real Data vs Dummy Data")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: CoinGlass Provider direct
    print("\n1️⃣ Testing CoinGlassProvider directly...")
    provider = CoinGlassProvider()
    
    if not provider.api_key:
        print("❌ COINGLASS_API_KEY not found")
        return False
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in test_symbols:
        print(f"\n🔄 Testing {symbol}...")
        
        # Test ticker
        ticker = provider.get_futures_ticker(symbol)
        if 'error' not in ticker:
            price = ticker.get('price', 0)
            print(f"  📊 Ticker Price: ${price:.2f}")
            
            # Check if it's dummy data
            if symbol == 'BTCUSDT' and abs(price - 70000) < 1000:
                print(f"  ⚠️ WARNING: Price {price} looks like dummy data!")
            else:
                print(f"  ✅ Price {price} appears to be real market data")
        else:
            print(f"  ❌ Ticker error: {ticker['error']}")
        
        # Test long/short ratio
        ls_ratio = provider.get_long_short_ratio(symbol)
        if 'error' not in ls_ratio:
            long_pct = ls_ratio.get('long_ratio', 50)
            print(f"  📊 Long/Short: {long_pct:.1f}% / {100-long_pct:.1f}%")
            
            # Check if it's realistic ratio
            if 20 <= long_pct <= 80:
                print(f"  ✅ L/S ratio {long_pct:.1f}% is realistic")
            else:
                print(f"  ⚠️ L/S ratio {long_pct:.1f}% might be unrealistic")
        else:
            print(f"  ❌ L/S ratio error: {ls_ratio['error']}")
        
        # Test open interest
        oi_data = provider.get_open_interest_chart(symbol)
        if 'error' not in oi_data:
            oi_value = oi_data.get('open_interest', 0)
            oi_change = oi_data.get('oi_change_percent', 0)
            print(f"  📊 Open Interest: ${oi_value/1000000:.1f}M ({oi_change:+.1f}%)")
            
            if oi_value > 0:
                print(f"  ✅ OI data appears real: ${oi_value/1000000:.1f}M")
            else:
                print(f"  ⚠️ OI data might be missing or dummy")
        else:
            print(f"  ❌ OI error: {oi_data['error']}")
    
    # Test 2: CryptoAPI integration
    print("\n2️⃣ Testing CryptoAPI integration...")
    crypto_api = CryptoAPI()
    
    btc_price = crypto_api.get_crypto_price('BTC')
    if 'error' not in btc_price:
        price = btc_price.get('price', 0)
        source = btc_price.get('source', 'unknown')
        print(f"  📊 BTC Price: ${price:.2f} (Source: {source})")
        
        # Check for dummy price patterns
        if abs(price - 70000) < 1000:
            print(f"  ⚠️ WARNING: BTC price ${price:.2f} looks like dummy data!")
        else:
            print(f"  ✅ BTC price ${price:.2f} appears to be real")
    
    # Test 3: Supply/Demand analysis
    print("\n3️⃣ Testing Supply/Demand analysis...")
    snd_analysis = crypto_api.analyze_supply_demand('BTC')
    if 'error' not in snd_analysis:
        signal = snd_analysis.get('signal', 'HOLD')
        confidence = snd_analysis.get('confidence', 0)
        current_price = snd_analysis.get('current_price', 0)
        data_quality = snd_analysis.get('data_quality', 'unknown')
        
        print(f"  📊 SnD Signal: {signal} ({confidence}%)")
        print(f"  📊 Price: ${current_price:.2f}")
        print(f"  📊 Data Quality: {data_quality}")
        
        if current_price > 0 and confidence > 30:
            print(f"  ✅ SnD analysis working with real data")
        else:
            print(f"  ⚠️ SnD analysis might have issues")
    else:
        print(f"  ❌ SnD analysis error: {snd_analysis['error']}")
    
    print("\n📋 SUMMARY:")
    print("✅ If you see real market prices (not $70,000 for BTC)")
    print("✅ If long/short ratios are between 20-80%")
    print("✅ If open interest values are > 0")
    print("✅ If timestamps are recent")
    print("❌ Then CoinGlass V4 is providing REAL data!")
    
    return True

if __name__ == "__main__":
    test_real_data()
