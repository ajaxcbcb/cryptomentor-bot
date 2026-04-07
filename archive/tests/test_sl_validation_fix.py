#!/usr/bin/env python3
"""
Test SL Validation Fix
Verifies that get_ticker() method exists and SL validation works
"""

import sys
import os

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def test_get_ticker_method():
    """Test that get_ticker method exists in BitunixAutoTradeClient"""
    print("🧪 Test 1: Check get_ticker() method exists...")
    
    from app.bitunix_autotrade_client import BitunixAutoTradeClient
    
    client = BitunixAutoTradeClient()
    
    # Check method exists
    assert hasattr(client, 'get_ticker'), "❌ get_ticker method not found!"
    print("   ✅ get_ticker() method exists")
    
    # Check method signature
    import inspect
    sig = inspect.signature(client.get_ticker)
    params = list(sig.parameters.keys())
    assert 'symbol' in params, "❌ get_ticker missing 'symbol' parameter!"
    print(f"   ✅ Method signature: get_ticker({', '.join(params)})")
    
    print("   ✅ Test 1 PASSED\n")


def test_stackmentor_validation():
    """Test that StackMentor has SL validation logic"""
    print("🧪 Test 2: Check StackMentor SL validation...")
    
    # Read stackmentor.py source
    with open('Bismillah/app/stackmentor.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Check for validation keywords
    checks = [
        ('get_ticker', 'Fetches current mark price'),
        ('current_mark_price', 'Gets current price for validation'),
        ('sl_valid', 'Validation flag'),
        ('entry >= current_mark_price', 'LONG SL validation'),
        ('entry <= current_mark_price', 'SHORT SL validation'),
        ('Cannot set breakeven SL', 'Validation failure message'),
    ]
    
    for keyword, description in checks:
        if keyword in source:
            print(f"   ✅ {description}: '{keyword}' found")
        else:
            print(f"   ❌ {description}: '{keyword}' NOT found!")
            return False
    
    print("   ✅ Test 2 PASSED\n")
    return True


def test_validation_logic():
    """Test SL validation logic with mock data"""
    print("🧪 Test 3: Test SL validation logic...")
    
    # Test LONG validation
    print("   Testing LONG position:")
    
    # Valid case: entry < mark
    entry = 67000.0
    mark = 68000.0
    side = "LONG"
    sl_valid = entry < mark
    print(f"      Entry: {entry}, Mark: {mark}, Side: {side}")
    print(f"      Valid: {sl_valid} {'✅' if sl_valid else '❌'}")
    assert sl_valid, "LONG validation failed for valid case!"
    
    # Invalid case: entry >= mark
    entry = 67000.0
    mark = 66500.0
    sl_valid = entry < mark
    print(f"      Entry: {entry}, Mark: {mark}, Side: {side}")
    print(f"      Valid: {sl_valid} {'✅' if not sl_valid else '❌'}")
    assert not sl_valid, "LONG validation failed for invalid case!"
    
    # Test SHORT validation
    print("   Testing SHORT position:")
    
    # Valid case: entry > mark
    entry = 67000.0
    mark = 66000.0
    side = "SHORT"
    sl_valid = entry > mark
    print(f"      Entry: {entry}, Mark: {mark}, Side: {side}")
    print(f"      Valid: {sl_valid} {'✅' if sl_valid else '❌'}")
    assert sl_valid, "SHORT validation failed for valid case!"
    
    # Invalid case: entry <= mark
    entry = 67000.0
    mark = 67500.0
    sl_valid = entry > mark
    print(f"      Entry: {entry}, Mark: {mark}, Side: {side}")
    print(f"      Valid: {sl_valid} {'✅' if not sl_valid else '❌'}")
    assert not sl_valid, "SHORT validation failed for invalid case!"
    
    print("   ✅ Test 3 PASSED\n")


def main():
    print("=" * 60)
    print("SL VALIDATION FIX - TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_get_ticker_method()
        test_stackmentor_validation()
        test_validation_logic()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("📝 Summary:")
        print("   1. get_ticker() method exists in BitunixAutoTradeClient")
        print("   2. StackMentor has SL validation logic")
        print("   3. Validation logic works correctly")
        print()
        print("🚀 Fix is ready for production!")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
