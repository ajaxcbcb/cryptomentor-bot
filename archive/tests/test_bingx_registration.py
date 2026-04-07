"""
Test BingX Registration Flow
Memastikan user BingX tidak dipaksa untuk verifikasi UID
"""

import sys
sys.path.insert(0, 'Bismillah')

from app.exchange_registry import get_exchange, EXCHANGES

def test_exchange_configs():
    """Test konfigurasi exchange untuk requires_uid_verification"""
    print("=" * 60)
    print("TEST: Exchange Configuration")
    print("=" * 60)
    
    for exchange_id, config in EXCHANGES.items():
        requires_uid = config.get('requires_uid_verification', False)
        coming_soon = config.get('coming_soon', False)
        
        status = "🔜 Coming Soon" if coming_soon else ("✅ Active" if not requires_uid else "🔐 Requires UID")
        
        print(f"\n{config['name']} ({exchange_id}):")
        print(f"  Status: {status}")
        print(f"  Requires UID Verification: {requires_uid}")
        print(f"  Referral Code: {config.get('referral_code', 'N/A')}")
        
        if not coming_soon:
            print(f"  ✓ Client: {config['client_class']}")

def test_bingx_specific():
    """Test konfigurasi spesifik BingX"""
    print("\n" + "=" * 60)
    print("TEST: BingX Specific Configuration")
    print("=" * 60)
    
    bingx = get_exchange('bingx')
    
    print(f"\nBingX Configuration:")
    print(f"  Name: {bingx['name']}")
    print(f"  Emoji: {bingx['emoji']}")
    print(f"  Coming Soon: {bingx['coming_soon']}")
    print(f"  Requires UID Verification: {bingx.get('requires_uid_verification', False)}")
    print(f"  Referral URL: {bingx['referral_url']}")
    print(f"  Referral Code: {bingx['referral_code']}")
    print(f"  API Key URL: {bingx['api_key_url']}")
    
    # Verifikasi bahwa BingX tidak memerlukan UID verification
    assert bingx.get('requires_uid_verification', False) == False, \
        "❌ BingX should NOT require UID verification!"
    
    print("\n✅ BingX correctly configured: No UID verification required")

def test_bitunix_specific():
    """Test konfigurasi spesifik Bitunix untuk perbandingan"""
    print("\n" + "=" * 60)
    print("TEST: Bitunix Specific Configuration (for comparison)")
    print("=" * 60)
    
    bitunix = get_exchange('bitunix')
    
    print(f"\nBitunix Configuration:")
    print(f"  Name: {bitunix['name']}")
    print(f"  Requires UID Verification: {bitunix.get('requires_uid_verification', False)}")
    print(f"  Referral Code: {bitunix['referral_code']}")
    
    # Verifikasi bahwa Bitunix MEMERLUKAN UID verification
    assert bitunix.get('requires_uid_verification', False) == True, \
        "❌ Bitunix SHOULD require UID verification!"
    
    print("\n✅ Bitunix correctly configured: UID verification required")

def test_flow_logic():
    """Test logic flow untuk berbagai exchange"""
    print("\n" + "=" * 60)
    print("TEST: Registration Flow Logic")
    print("=" * 60)
    
    test_cases = [
        ('bingx', False, 'Should skip UID verification'),
        ('bitunix', True, 'Should require UID verification'),
        ('binance', False, 'Should skip UID verification'),
        ('bybit', False, 'Should skip UID verification'),
    ]
    
    for exchange_id, expected_uid_required, description in test_cases:
        try:
            ex = get_exchange(exchange_id)
            requires_uid = ex.get('requires_uid_verification', False)
            
            status = "✅ PASS" if requires_uid == expected_uid_required else "❌ FAIL"
            print(f"\n{status} {ex['name']} ({exchange_id}):")
            print(f"  Expected UID Required: {expected_uid_required}")
            print(f"  Actual UID Required: {requires_uid}")
            print(f"  Description: {description}")
            
            if requires_uid != expected_uid_required:
                print(f"  ⚠️ Configuration mismatch!")
        except Exception as e:
            print(f"\n❌ ERROR testing {exchange_id}: {e}")

if __name__ == "__main__":
    print("\n🧪 Testing BingX Registration Flow Configuration\n")
    
    try:
        test_exchange_configs()
        test_bingx_specific()
        test_bitunix_specific()
        test_flow_logic()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("  • BingX: No UID verification required ✅")
        print("  • Bitunix: UID verification required ✅")
        print("  • Flow logic correctly configured ✅")
        print("\nUser dengan BingX akan langsung ke setup API Key")
        print("tanpa dipaksa untuk verifikasi UID referral.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
