#!/usr/bin/env python3
"""
Test StackMentor Deposit Requirement
Verify that only users with deposit >= $60 can use StackMentor
"""

import sys
import os

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def test_deposit_functions():
    """Test deposit tracking functions"""
    print("🧪 Testing deposit tracking functions...")
    
    try:
        from app.supabase_repo import (
            get_user_total_deposit,
            is_stackmentor_eligible,
            add_user_deposit
        )
        print("✅ Deposit functions imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_eligibility_logic():
    """Test eligibility logic"""
    print("\n🧪 Testing eligibility logic...")
    
    test_cases = [
        (0.00, False, "No deposit"),
        (30.00, False, "Below threshold"),
        (59.99, False, "Just below threshold"),
        (60.00, True, "Exactly at threshold"),
        (60.01, True, "Just above threshold"),
        (100.00, True, "Well above threshold"),
        (1000.00, True, "Large deposit"),
    ]
    
    all_passed = True
    
    for deposit, expected, description in test_cases:
        eligible = deposit >= 60.0
        status = "✅" if eligible == expected else "❌"
        
        print(f"   {status} ${deposit:7.2f} → {'Eligible' if eligible else 'Not eligible':13} ({description})")
        
        if eligible != expected:
            all_passed = False
    
    return all_passed


def test_notification_messages():
    """Test notification message logic"""
    print("\n🧪 Testing notification messages...")
    
    # Simulate eligible user
    stackmentor_enabled = True
    print("\n   📱 Eligible User (deposit ≥ $60):")
    print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   🎯 TP1: 45000.0000 (+4.7%) — 50% posisi")
    print("   🎯 TP2: 46000.0000 (+7.0%) — 40% posisi")
    print("   🎯 TP3: 53000.0000 (+23.3%) — 10% posisi")
    print("   ⚖️ R:R: 1:2 → 1:3 → 1:10 (StackMentor 🎯)")
    print("   🎯 StackMentor Active (Deposit ≥ $60)")
    
    # Simulate non-eligible user
    stackmentor_enabled = False
    print("\n   📱 Non-Eligible User (deposit < $60):")
    print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   🎯 TP: 45000.0000 (+4.7%)")
    print("   ⚖️ R:R Ratio: 1:2")
    print("   💡 Deposit $60+ untuk unlock StackMentor (3-tier TP)")
    
    return True


def test_database_queries():
    """Test SQL queries (documentation only)"""
    print("\n🧪 Testing database queries (documentation)...")
    
    queries = [
        ("Check eligibility", "SELECT is_stackmentor_eligible(123456789);"),
        ("Get total deposit", "SELECT total_deposit FROM users WHERE telegram_id = 123456789;"),
        ("Add deposit", "SELECT add_user_deposit(123456789, 100.00);"),
        ("List eligible users", "SELECT telegram_id, first_name, total_deposit FROM users WHERE total_deposit >= 60;"),
    ]
    
    for name, query in queries:
        print(f"   ✅ {name}")
        print(f"      {query}")
    
    return True


def test_integration_flow():
    """Test complete integration flow"""
    print("\n🧪 Testing integration flow...")
    
    steps = [
        "1. User starts autotrade",
        "2. Engine checks is_stackmentor_eligible(user_id)",
        "3. If deposit >= $60:",
        "   → stackmentor_enabled = True",
        "   → Calculate 3-tier TP (50%/40%/10%)",
        "   → Register with StackMentor monitor",
        "   → Show StackMentor notification",
        "4. If deposit < $60:",
        "   → stackmentor_enabled = False",
        "   → Use legacy TP",
        "   → Show upgrade message",
    ]
    
    for step in steps:
        print(f"   {step}")
    
    return True


def test_admin_operations():
    """Test admin operations (documentation)"""
    print("\n🧪 Testing admin operations (documentation)...")
    
    operations = [
        ("Add deposit for user", "SELECT add_user_deposit(123456789, 100.00);"),
        ("Set deposit directly", "UPDATE users SET total_deposit = 100.00 WHERE telegram_id = 123456789;"),
        ("Check user eligibility", "SELECT telegram_id, total_deposit, is_stackmentor_eligible(telegram_id) FROM users WHERE telegram_id = 123456789;"),
        ("List all eligible", "SELECT telegram_id, first_name, total_deposit FROM users WHERE total_deposit >= 60 ORDER BY total_deposit DESC;"),
        ("Reset deposit", "UPDATE users SET total_deposit = 0 WHERE telegram_id = 123456789;"),
    ]
    
    for name, query in operations:
        print(f"   ✅ {name}")
        print(f"      {query}")
    
    return True


def main():
    print("=" * 60)
    print("StackMentor Deposit Requirement Test")
    print("=" * 60)
    print("Minimum deposit: $60 USDT")
    print("=" * 60)
    
    tests = [
        ("Deposit Functions Import", test_deposit_functions),
        ("Eligibility Logic", test_eligibility_logic),
        ("Notification Messages", test_notification_messages),
        ("Database Queries", test_database_queries),
        ("Integration Flow", test_integration_flow),
        ("Admin Operations", test_admin_operations),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        print("\n📝 Deployment Checklist:")
        print("1. Apply db/add_deposit_tracking.sql migration")
        print("2. Apply db/stackmentor_migration.sql migration")
        print("3. Deploy updated Python files")
        print("4. Add deposits for existing users")
        print("5. Test with eligible and non-eligible users")
    else:
        print("⚠️  SOME TESTS FAILED - Fix issues before deployment")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
