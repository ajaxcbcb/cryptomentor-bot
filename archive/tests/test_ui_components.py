#!/usr/bin/env python3
"""
Test UI Components
Quick test to verify all UI components work correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Bismillah'))

from app.ui_components import (
    progress_indicator,
    onboarding_welcome,
    error_message_actionable,
    loading_message,
    success_message,
    comparison_card,
    settings_group,
    section_header,
    status_badge,
    format_currency,
    format_percentage,
)

def test_progress_indicator():
    print("=" * 50)
    print("TEST: Progress Indicator")
    print("=" * 50)
    result = progress_indicator(2, 4, "Setup API Key")
    print(result)
    assert "50%" in result
    assert "Step 2/4" in result
    print("✅ PASS\n")

def test_onboarding_welcome():
    print("=" * 50)
    print("TEST: Onboarding Welcome")
    print("=" * 50)
    result = onboarding_welcome(total_steps=4)
    print(result)
    assert "Welcome" in result
    assert "4 langkah" in result
    print("✅ PASS\n")

def test_comparison_card():
    print("=" * 50)
    print("TEST: Comparison Card")
    print("=" * 50)
    result = comparison_card(
        title="REKOMENDASI",
        emoji="🌟",
        pros=["Otomatis hitung margin", "Safe compounding"],
        cons=["Butuh pengalaman"],
        badge="✨ 95% user pilih ini"
    )
    print(result)
    assert "REKOMENDASI" in result
    assert "Otomatis hitung margin" in result
    print("✅ PASS\n")

def test_loading_message():
    print("=" * 50)
    print("TEST: Loading Message")
    print("=" * 50)
    result = loading_message(
        action="Verifying connection",
        tip="Risk-based mode helps you survive 50+ losing trades!"
    )
    print(result)
    assert "Verifying connection" in result
    assert "Tip:" in result
    print("✅ PASS\n")

def test_success_message():
    print("=" * 50)
    print("TEST: Success Message")
    print("=" * 50)
    result = success_message(
        "Setup Complete!",
        {
            "Mode": "🎯 Rekomendasi",
            "Balance": "$100.00 USDT",
            "Risk": "2%"
        }
    )
    print(result)
    assert "Setup Complete" in result
    assert "Mode:" in result
    assert "Balance:" in result
    print("✅ PASS\n")

def test_settings_group():
    print("=" * 50)
    print("TEST: Settings Group")
    print("=" * 50)
    result = settings_group(
        title="CURRENT STATUS",
        emoji="📊",
        items=[
            "Mode: 🎯 Rekomendasi",
            "Balance: $100 USDT",
            "Risk: 2%"
        ],
        show_divider=True
    )
    print(result)
    assert "CURRENT STATUS" in result
    assert "Mode:" in result
    print("✅ PASS\n")

def test_section_header():
    print("=" * 50)
    print("TEST: Section Header")
    print("=" * 50)
    result = section_header("AUTOTRADE SETTINGS", "⚙️")
    print(result)
    assert "AUTOTRADE SETTINGS" in result
    assert "⚙️" in result
    print("✅ PASS\n")

def test_status_badge():
    print("=" * 50)
    print("TEST: Status Badge")
    print("=" * 50)
    active = status_badge(True)
    inactive = status_badge(False)
    print(f"Active: {active}")
    print(f"Inactive: {inactive}")
    assert "🟢" in active
    assert "🔴" in inactive
    print("✅ PASS\n")

def test_format_currency():
    print("=" * 50)
    print("TEST: Format Currency")
    print("=" * 50)
    result = format_currency(1234.56)
    print(result)
    assert "$1,234.56" in result
    assert "USDT" in result
    print("✅ PASS\n")

def test_format_percentage():
    print("=" * 50)
    print("TEST: Format Percentage")
    print("=" * 50)
    positive = format_percentage(12.34)
    negative = format_percentage(-5.67)
    print(f"Positive: {positive}")
    print(f"Negative: {negative}")
    assert "+12.34%" in positive
    assert "-5.67%" in negative
    print("✅ PASS\n")

def test_error_message_actionable():
    print("=" * 50)
    print("TEST: Error Message Actionable")
    print("=" * 50)
    result = error_message_actionable(
        title="❌ API Key Ditolak",
        steps=[
            {'num': '1️⃣', 'emoji': '🌐', 'text': 'Buka API Management'},
            {'num': '2️⃣', 'emoji': '🗑️', 'text': 'Hapus API Key lama'},
        ],
        help_options=["📹 Video Tutorial", "💬 Chat Admin"]
    )
    print(result)
    assert "API Key Ditolak" in result
    assert "Buka API Management" in result
    assert "Video Tutorial" in result
    print("✅ PASS\n")

def main():
    print("\n" + "=" * 50)
    print("UI COMPONENTS TEST SUITE")
    print("=" * 50 + "\n")
    
    tests = [
        test_progress_indicator,
        test_onboarding_welcome,
        test_comparison_card,
        test_loading_message,
        test_success_message,
        test_settings_group,
        test_section_header,
        test_status_badge,
        test_format_currency,
        test_format_percentage,
        test_error_message_actionable,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ FAIL: {test.__name__}")
            print(f"Error: {e}\n")
            failed += 1
    
    print("=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 All tests passed! UI components are ready to deploy.")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix before deploying.")
        return 1

if __name__ == "__main__":
    exit(main())
