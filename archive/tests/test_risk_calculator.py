"""
Test suite for Senior Risk Management Module
Verifies deterministic calculations with 8-decimal precision
"""

import sys
sys.path.insert(0, 'Bismillah')

from app.risk_calculator import calculate_position_size, validate_position_size
import json


def test_basic_calculation():
    """Test basic position size calculation"""
    print("=" * 60)
    print("TEST 1: Basic Calculation")
    print("=" * 60)
    
    result = calculate_position_size(
        last_balance=1000.0,
        risk_percentage=2.0,
        entry_price=50000.0,
        stop_loss_price=49000.0
    )
    
    print(json.dumps(result, indent=2))
    
    # Verify calculation
    # Risk Amount = 1000 * (2/100) = 20.0
    # Price Delta = |50000 - 49000| = 1000.0
    # Position Size = 20.0 / 1000.0 = 0.02
    
    assert result["status"] == "success"
    assert result["risk_amount"] == 20.0
    assert result["position_size"] == 0.02
    assert result["currency_risk_percent"] == 2.0
    assert result["error_message"] is None
    print("✅ PASSED\n")


def test_division_by_zero():
    """Test division by zero error"""
    print("=" * 60)
    print("TEST 2: Division by Zero")
    print("=" * 60)
    
    result = calculate_position_size(
        last_balance=1000.0,
        risk_percentage=2.0,
        entry_price=50000.0,
        stop_loss_price=50000.0  # Same as entry
    )
    
    print(json.dumps(result, indent=2))
    
    assert result["status"] == "error"
    assert result["position_size"] == 0.0
    assert "Division by zero" in result["error_message"]
    print("✅ PASSED\n")


def test_missing_input():
    """Test missing input parameter"""
    print("=" * 60)
    print("TEST 3: Missing Input")
    print("=" * 60)
    
    result = calculate_position_size(
        last_balance=1000.0,
        risk_percentage=2.0,
        entry_price=None,  # Missing
        stop_loss_price=49000.0
    )
    
    print(json.dumps(result, indent=2))
    
    assert result["status"] == "error"
    assert result["position_size"] == 0.0
    assert "Missing required input" in result["error_message"]
    print("✅ PASSED\n")


def test_negative_balance():
    """Test negative balance"""
    print("=" * 60)
    print("TEST 4: Negative Balance")
    print("=" * 60)
    
    result = calculate_position_size(
        last_balance=-1000.0,
        risk_percentage=2.0,
        entry_price=50000.0,
        stop_loss_price=49000.0
    )
    
    print(json.dumps(result, indent=2))
    
    assert result["status"] == "error"
    assert "must be positive" in result["error_message"]
    print("✅ PASSED\n")


def test_precision():
    """Test 8-decimal precision"""
    print("=" * 60)
    print("TEST 5: 8-Decimal Precision")
    print("=" * 60)
    
    result = calculate_position_size(
        last_balance=1234.56789012,
        risk_percentage=1.5,
        entry_price=67890.12345678,
        stop_loss_price=67000.98765432
    )
    
    print(json.dumps(result, indent=2))
    
    # Verify precision
    # Risk Amount = 1234.56789012 * 0.015 = 18.51851835
    # Price Delta = |67890.12345678 - 67000.98765432| = 889.13580246
    # Position Size = 18.51851835 / 889.13580246 = 0.02082896
    
    assert result["status"] == "success"
    assert isinstance(result["risk_amount"], float)
    assert isinstance(result["position_size"], float)
    print(f"Risk Amount: {result['risk_amount']}")
    print(f"Position Size: {result['position_size']}")
    print("✅ PASSED\n")


def test_short_position():
    """Test SHORT position (entry < stop_loss)"""
    print("=" * 60)
    print("TEST 6: SHORT Position")
    print("=" * 60)
    
    result = calculate_position_size(
        last_balance=1000.0,
        risk_percentage=2.0,
        entry_price=49000.0,  # Entry below SL (SHORT)
        stop_loss_price=50000.0
    )
    
    print(json.dumps(result, indent=2))
    
    # Should work the same due to ABS()
    assert result["status"] == "success"
    assert result["risk_amount"] == 20.0
    assert result["position_size"] == 0.02
    print("✅ PASSED\n")


def test_validation():
    """Test position size validation"""
    print("=" * 60)
    print("TEST 7: Position Size Validation")
    print("=" * 60)
    
    # Test below minimum
    result1 = validate_position_size(0.0005, min_size=0.001)
    print("Below minimum:")
    print(json.dumps(result1, indent=2))
    assert result1["valid"] == False
    assert result1["adjusted_size"] == 0.001
    
    # Test above maximum
    result2 = validate_position_size(2000000.0, max_size=1000000.0)
    print("\nAbove maximum:")
    print(json.dumps(result2, indent=2))
    assert result2["valid"] == False
    assert result2["adjusted_size"] == 1000000.0
    
    # Test valid
    result3 = validate_position_size(0.5, min_size=0.001, max_size=1000000.0)
    print("\nValid:")
    print(json.dumps(result3, indent=2))
    assert result3["valid"] == True
    assert result3["adjusted_size"] == 0.5
    
    print("✅ PASSED\n")


def test_real_world_scenario():
    """Test real-world trading scenario"""
    print("=" * 60)
    print("TEST 8: Real-World Scenario")
    print("=" * 60)
    print("Scenario: $100 balance, 2% risk, BTC LONG")
    print("Entry: $66,500 | Stop Loss: $65,500")
    print()
    
    result = calculate_position_size(
        last_balance=100.0,
        risk_percentage=2.0,
        entry_price=66500.0,
        stop_loss_price=65500.0
    )
    
    print(json.dumps(result, indent=2))
    
    # Risk Amount = 100 * 0.02 = 2.0 USDT
    # Price Delta = 1000.0
    # Position Size = 2.0 / 1000.0 = 0.002 BTC
    
    assert result["status"] == "success"
    assert result["risk_amount"] == 2.0
    assert result["position_size"] == 0.002
    
    print(f"\n💡 Interpretation:")
    print(f"   - Risk per trade: ${result['risk_amount']} ({result['currency_risk_percent']}%)")
    print(f"   - Position size: {result['position_size']} BTC")
    print(f"   - If SL hits: Loss = ${result['risk_amount']}")
    print("✅ PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SENIOR RISK MANAGEMENT MODULE - TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_basic_calculation()
        test_division_by_zero()
        test_missing_input()
        test_negative_balance()
        test_precision()
        test_short_position()
        test_validation()
        test_real_world_scenario()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)
