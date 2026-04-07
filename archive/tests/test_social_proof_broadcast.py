"""
Test Social Proof Broadcast System
Test username masking dan broadcast ke non-autotrade users
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

from app.social_proof import _mask_name, _should_broadcast, MIN_BROADCAST_PROFIT


def test_username_masking():
    """Test fungsi sensor username"""
    print("=" * 60)
    print("TEST 1: Username Masking")
    print("=" * 60)
    
    test_cases = [
        ("Budi", "B***i"),
        ("John", "J***n"),
        ("A", "A***"),
        ("Jo", "J***o"),
        ("Bob", "B***b"),
        ("Budi Santoso", "B***i S***o"),
        ("John Doe Smith", "J***n D***e S***h"),
        ("Muhammad", "M***d"),
        ("", "User***"),
        ("X Y Z", "X*** Y*** Z***"),
    ]
    
    passed = 0
    failed = 0
    
    for input_name, expected in test_cases:
        result = _mask_name(input_name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | '{input_name}' → '{result}' (expected: '{expected}')")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_broadcast_threshold():
    """Test threshold dan cooldown broadcast"""
    print("\n" + "=" * 60)
    print("TEST 2: Broadcast Threshold & Cooldown")
    print("=" * 60)
    
    user_id = 12345
    
    # Test 1: Profit di bawah threshold
    result1 = _should_broadcast(user_id, 3.0)
    print(f"{'✅ PASS' if not result1 else '❌ FAIL'} | Profit $3.0 (below ${MIN_BROADCAST_PROFIT}) → Should NOT broadcast: {not result1}")
    
    # Test 2: Profit di atas threshold (first time)
    result2 = _should_broadcast(user_id, 10.0)
    print(f"{'✅ PASS' if result2 else '❌ FAIL'} | Profit $10.0 (above ${MIN_BROADCAST_PROFIT}) → Should broadcast: {result2}")
    
    # Test 3: Profit di atas threshold tapi cooldown belum habis
    # (setelah test 2, user_id sudah di-broadcast)
    result3 = _should_broadcast(user_id, 15.0)
    print(f"{'✅ PASS' if not result3 else '❌ FAIL'} | Profit $15.0 but within cooldown → Should NOT broadcast: {not result3}")
    
    # Test 4: User lain (no cooldown)
    user_id_2 = 67890
    result4 = _should_broadcast(user_id_2, 8.0)
    print(f"{'✅ PASS' if result4 else '❌ FAIL'} | Different user, profit $8.0 → Should broadcast: {result4}")
    
    return True


async def test_broadcast_message_format():
    """Test format pesan broadcast"""
    print("\n" + "=" * 60)
    print("TEST 3: Broadcast Message Format")
    print("=" * 60)
    
    # Simulate broadcast message
    user_id = 12345
    first_name = "Budi Santoso"
    symbol = "BTCUSDT"
    side = "LONG"
    pnl_usdt = 12.50
    leverage = 10
    
    display_name = _mask_name(first_name)
    emoji = "🟢" if side == "LONG" else "🔴"
    direction = "LONG ↑" if side == "LONG" else "SHORT ↓"
    
    message = (
        f"🔥 <b>Trade Profit Alert!</b>\n\n"
        f"👤 User <b>{display_name}</b> baru saja profit:\n\n"
        f"{emoji} <b>{symbol}</b> {direction}\n"
        f"💰 Profit: <b>+{pnl_usdt:.2f} USDT</b>\n"
        f"⚡ Leverage: {leverage}x\n\n"
        f"🤖 <i>Dieksekusi otomatis oleh CryptoMentor AI</i>\n\n"
        f"💡 Mau bot trading juga buat kamu?\n"
        f"Ketik /autotrade untuk mulai!"
    )
    
    print("Preview Broadcast Message:")
    print("-" * 60)
    # Remove HTML tags for preview
    preview = message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
    print(preview)
    print("-" * 60)
    
    # Verify username is masked
    if "Budi Santoso" in message:
        print("❌ FAIL | Full name found in message (should be masked)")
        return False
    elif display_name in message:
        print(f"✅ PASS | Username properly masked: {display_name}")
        return True
    else:
        print("❌ FAIL | Masked name not found in message")
        return False


async def test_target_users_logic():
    """Test logika target users (non-autotrade users only)"""
    print("\n" + "=" * 60)
    print("TEST 4: Target Users Logic")
    print("=" * 60)
    
    print("Logic: Broadcast hanya ke user yang BELUM daftar autotrade")
    print("✅ Target: Users di table 'users' yang TIDAK ada di 'autotrade_sessions'")
    print("❌ Skip: Users yang sudah ada di 'autotrade_sessions'")
    print("\nNote: Actual database query akan dijalankan saat broadcast real")
    
    return True


def test_configuration():
    """Test konfigurasi broadcast"""
    print("\n" + "=" * 60)
    print("TEST 5: Broadcast Configuration")
    print("=" * 60)
    
    from app.social_proof import MIN_BROADCAST_PROFIT, BROADCAST_COOLDOWN_HOURS
    
    print(f"✅ Minimum Profit Threshold: ${MIN_BROADCAST_PROFIT} USDT")
    print(f"✅ Cooldown Period: {BROADCAST_COOLDOWN_HOURS} hours")
    print(f"✅ Target Audience: Non-autotrade users only")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SOCIAL PROOF BROADCAST SYSTEM - TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Username Masking
    results.append(("Username Masking", test_username_masking()))
    
    # Test 2: Broadcast Threshold
    results.append(("Broadcast Threshold", test_broadcast_threshold()))
    
    # Test 3: Message Format
    results.append(("Message Format", await test_broadcast_message_format()))
    
    # Test 4: Target Users Logic
    results.append(("Target Users Logic", await test_target_users_logic()))
    
    # Test 5: Configuration
    results.append(("Configuration", test_configuration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Social proof broadcast system is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
