
#!/usr/bin/env python3
"""
Test script for the fixed /analyze command
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_assistant import AIAssistant
from crypto_api import CryptoAPI

def test_analyze_command():
    """Test the analyze command with real data"""
    print("🔍 Testing /analyze command...")
    
    # Initialize components
    crypto_api = CryptoAPI()
    ai_assistant = AIAssistant()
    
    # Test symbols
    test_symbols = ['BTC', 'ETH']
    
    for symbol in test_symbols:
        print(f"\n📊 Testing analysis for {symbol}...")
        
        # Test comprehensive analysis
        try:
            analysis = ai_assistant.get_comprehensive_analysis(
                symbol=symbol,
                crypto_api=crypto_api
            )
            
            print(f"✅ Analysis completed for {symbol}")
            print(f"📝 Analysis length: {len(analysis)} characters")
            
            # Check for key components
            if "Support" in analysis and "Resistance" in analysis:
                print("✅ Support & Resistance included")
            else:
                print("⚠️ Support & Resistance missing")
                
            if "CoinGlass" in analysis:
                print("✅ CoinGlass data included")
            else:
                print("⚠️ CoinGlass data missing")
                
            if "CoinMarketCap" in analysis:
                print("✅ CoinMarketCap data included")
            else:
                print("⚠️ CoinMarketCap data missing")
                
            # Show first 200 characters
            print(f"📄 Preview: {analysis[:200]}...")
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 CryptoMentor AI - Analyze Command Test")
    print("=" * 50)
    
    # Check API keys
    cmc_key = os.getenv("COINMARKETCAP_API_KEY") or os.getenv("CMC_API_KEY")
    cg_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
    
    print(f"🔑 API Keys Status:")
    print(f"  CoinMarketCap: {'✅ Available' if cmc_key else '❌ Missing'}")
    print(f"  CoinGlass: {'✅ Available' if cg_key else '❌ Missing'}")
    
    if not cmc_key and not cg_key:
        print("❌ No API keys found! Please set environment variables.")
        sys.exit(1)
    
    test_analyze_command()
    print("\n✅ Test completed!")
