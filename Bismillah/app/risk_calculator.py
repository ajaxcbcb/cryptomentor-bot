"""
Senior Risk Management Module
Deterministic capital preservation calculations with strict mathematical constraints.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def calculate_position_size(
    last_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss_price: float
) -> Dict[str, Any]:
    """
    Execute deterministic capital preservation calculations.
    
    Logic Engine:
    1. Validation: Ensure all inputs are present and positive
    2. Risk Calculation: Risk Amount = last_balance * (risk_percentage / 100)
    3. Delta Calculation: Price Delta = ABS(entry_price - stop_loss_price)
    4. Size Calculation: Position Size = Risk Amount / Price Delta
    
    Args:
        last_balance: Current account balance (float)
        risk_percentage: Risk per trade as percentage (float, e.g., 2.0 for 2%)
        entry_price: Entry price for the position (float)
        stop_loss_price: Stop loss price (float)
    
    Returns:
        Dict with keys:
        - risk_amount: float (8 decimal precision)
        - position_size: float (8 decimal precision)
        - currency_risk_percent: float (8 decimal precision)
        - status: str ("success" or "error")
        - error_message: str or None
    """
    
    # Step 1: Validation
    try:
        # Check if all inputs are present
        if last_balance is None or risk_percentage is None or entry_price is None or stop_loss_price is None:
            return {
                "risk_amount": 0.0,
                "position_size": 0.0,
                "currency_risk_percent": 0.0,
                "status": "error",
                "error_message": "Missing required input parameters"
            }
        
        # Convert to float and validate positive values
        last_balance = float(last_balance)
        risk_percentage = float(risk_percentage)
        entry_price = float(entry_price)
        stop_loss_price = float(stop_loss_price)
        
        if last_balance <= 0:
            return {
                "risk_amount": 0.0,
                "position_size": 0.0,
                "currency_risk_percent": 0.0,
                "status": "error",
                "error_message": "last_balance must be positive"
            }
        
        if risk_percentage <= 0:
            return {
                "risk_amount": 0.0,
                "position_size": 0.0,
                "currency_risk_percent": 0.0,
                "status": "error",
                "error_message": "risk_percentage must be positive"
            }
        
        if entry_price <= 0:
            return {
                "risk_amount": 0.0,
                "position_size": 0.0,
                "currency_risk_percent": 0.0,
                "status": "error",
                "error_message": "entry_price must be positive"
            }
        
        if stop_loss_price <= 0:
            return {
                "risk_amount": 0.0,
                "position_size": 0.0,
                "currency_risk_percent": 0.0,
                "status": "error",
                "error_message": "stop_loss_price must be positive"
            }
        
        # Check for division by zero
        if entry_price == stop_loss_price:
            return {
                "risk_amount": 0.0,
                "position_size": 0.0,
                "currency_risk_percent": 0.0,
                "status": "error",
                "error_message": "Division by zero: entry_price equals stop_loss_price"
            }
        
        # Step 2: Risk Calculation
        risk_amount = last_balance * (risk_percentage / 100.0)
        
        # Step 3: Delta Calculation
        price_delta = abs(entry_price - stop_loss_price)
        
        # Step 4: Size Calculation
        position_size = risk_amount / price_delta
        
        # Return with 8-decimal precision
        return {
            "risk_amount": round(risk_amount, 8),
            "position_size": round(position_size, 8),
            "currency_risk_percent": round(risk_percentage, 8),
            "status": "success",
            "error_message": None
        }
        
    except ValueError as e:
        return {
            "risk_amount": 0.0,
            "position_size": 0.0,
            "currency_risk_percent": 0.0,
            "status": "error",
            "error_message": f"Invalid input type: {str(e)}"
        }
    except Exception as e:
        logger.error(f"[RiskCalculator] Unexpected error: {e}")
        return {
            "risk_amount": 0.0,
            "position_size": 0.0,
            "currency_risk_percent": 0.0,
            "status": "error",
            "error_message": f"Calculation error: {str(e)}"
        }


def validate_position_size(
    position_size: float,
    min_size: float = 0.001,
    max_size: float = 1000000.0
) -> Dict[str, Any]:
    """
    Validate calculated position size against exchange constraints.
    
    Args:
        position_size: Calculated position size
        min_size: Minimum allowed position size
        max_size: Maximum allowed position size
    
    Returns:
        Dict with validation result
    """
    try:
        position_size = float(position_size)
        min_size = float(min_size)
        max_size = float(max_size)
        
        if position_size < min_size:
            return {
                "valid": False,
                "adjusted_size": min_size,
                "reason": f"Position size {position_size} below minimum {min_size}"
            }
        
        if position_size > max_size:
            return {
                "valid": False,
                "adjusted_size": max_size,
                "reason": f"Position size {position_size} exceeds maximum {max_size}"
            }
        
        return {
            "valid": True,
            "adjusted_size": position_size,
            "reason": None
        }
        
    except Exception as e:
        return {
            "valid": False,
            "adjusted_size": 0.0,
            "reason": f"Validation error: {str(e)}"
        }
