"""
Professional Position Sizing Module
Calculates position size based on risk percentage and stop loss distance.

This enables:
- Safe compounding as balance grows
- Account protection from blow-ups
- Consistent risk management
- Professional money management
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def calculate_position_size(
    balance: float,
    risk_pct: float,
    entry_price: float,
    sl_price: float,
    leverage: int,
    symbol: str = "BTCUSDT"
) -> Dict:
    """
    Calculate position size based on risk percentage.
    
    Formula:
    1. Risk Amount = Balance × Risk%
    2. SL Distance% = |Entry - SL| / Entry
    3. Position Size = Risk Amount / SL Distance%
    4. Margin Required = Position Size / Leverage
    5. Quantity = Position Size / Entry Price
    
    Args:
        balance: Current account balance in USDT
        risk_pct: Risk percentage (e.g., 2.0 for 2%)
        entry_price: Entry price for the trade
        sl_price: Stop loss price
        leverage: Leverage multiplier
        symbol: Trading pair symbol
    
    Returns:
        {
            'position_size_usdt': float,  # Total position value in USDT
            'margin_required': float,      # Margin needed to open position
            'qty': float,                  # Quantity to buy/sell
            'risk_amount': float,          # Max loss in USDT if SL hits
            'sl_distance_pct': float,      # Stop loss distance as percentage
            'valid': bool,                 # Whether calculation is valid
            'error': str,                  # Error message if invalid
        }
    
    Example:
        balance = 100 USDT
        risk_pct = 2.0 (2%)
        entry = 50000
        sl = 49000 (2% away)
        leverage = 10x
        
        Result:
        - Risk amount: $2 (2% of $100)
        - SL distance: 2%
        - Position size: $100 ($2 / 0.02)
        - Margin: $10 ($100 / 10x)
        - Qty: 0.002 BTC ($100 / $50000)
    """
    
    try:
        # Validate inputs
        if balance <= 0:
            return {
                'valid': False,
                'error': 'Balance must be positive',
                'position_size_usdt': 0,
                'margin_required': 0,
                'qty': 0,
                'risk_amount': 0,
                'sl_distance_pct': 0,
            }
        
        if risk_pct <= 0 or risk_pct > 10:
            return {
                'valid': False,
                'error': 'Risk percentage must be between 0 and 10%',
                'position_size_usdt': 0,
                'margin_required': 0,
                'qty': 0,
                'risk_amount': 0,
                'sl_distance_pct': 0,
            }
        
        if entry_price <= 0 or sl_price <= 0:
            return {
                'valid': False,
                'error': 'Entry and SL prices must be positive',
                'position_size_usdt': 0,
                'margin_required': 0,
                'qty': 0,
                'risk_amount': 0,
                'sl_distance_pct': 0,
            }
        
        if leverage <= 0:
            return {
                'valid': False,
                'error': 'Leverage must be positive',
                'position_size_usdt': 0,
                'margin_required': 0,
                'qty': 0,
                'risk_amount': 0,
                'sl_distance_pct': 0,
            }
        
        # Calculate risk amount
        risk_amount = balance * (risk_pct / 100.0)
        
        # Calculate SL distance as percentage
        sl_distance_pct = abs(entry_price - sl_price) / entry_price
        
        # Validate SL distance (must be reasonable)
        if sl_distance_pct < 0.001:  # Less than 0.1%
            return {
                'valid': False,
                'error': 'Stop loss too tight (< 0.1%)',
                'position_size_usdt': 0,
                'margin_required': 0,
                'qty': 0,
                'risk_amount': risk_amount,
                'sl_distance_pct': sl_distance_pct,
            }
        
        if sl_distance_pct > 0.15:  # More than 15%
            return {
                'valid': False,
                'error': 'Stop loss too wide (> 15%)',
                'position_size_usdt': 0,
                'margin_required': 0,
                'qty': 0,
                'risk_amount': risk_amount,
                'sl_distance_pct': sl_distance_pct,
            }
        
        # Calculate position size
        # Risk Amount = Position Size × SL Distance%
        # Position Size = Risk Amount / SL Distance%
        position_size_usdt = risk_amount / sl_distance_pct
        
        # Calculate margin required
        margin_required = position_size_usdt / leverage
        
        # Validate margin doesn't exceed balance
        if margin_required > balance:
            # Reduce position size to fit balance
            margin_required = balance * 0.95  # Use 95% max to leave buffer
            position_size_usdt = margin_required * leverage
            actual_risk = position_size_usdt * sl_distance_pct
            
            logger.warning(
                f"[PositionSizing] Margin capped at balance: "
                f"balance={balance:.2f}, original_margin={margin_required:.2f}, "
                f"capped_margin={margin_required:.2f}, actual_risk={actual_risk:.2f}"
            )
        
        # Calculate quantity
        qty = position_size_usdt / entry_price
        
        # Get quantity precision for symbol
        from app.autotrade_engine import QTY_PRECISION
        precision = QTY_PRECISION.get(symbol, 3)
        qty = round(qty, precision)
        
        # Validate minimum quantity
        min_qty = 10 ** (-precision) if precision > 0 else 1
        if qty < min_qty:
            return {
                'valid': False,
                'error': f'Quantity too small (min: {min_qty})',
                'position_size_usdt': position_size_usdt,
                'margin_required': margin_required,
                'qty': qty,
                'risk_amount': risk_amount,
                'sl_distance_pct': sl_distance_pct,
            }
        
        result = {
            'valid': True,
            'error': None,
            'position_size_usdt': round(position_size_usdt, 2),
            'margin_required': round(margin_required, 2),
            'qty': qty,
            'risk_amount': round(risk_amount, 2),
            'sl_distance_pct': round(sl_distance_pct * 100, 2),  # Convert to percentage
        }
        
        logger.info(
            f"[PositionSizing] Calculated for {symbol}: "
            f"balance={balance:.2f}, risk={risk_pct}%, "
            f"entry={entry_price:.2f}, sl={sl_price:.2f}, "
            f"sl_dist={result['sl_distance_pct']:.2f}%, "
            f"position={result['position_size_usdt']:.2f}, "
            f"margin={result['margin_required']:.2f}, "
            f"qty={result['qty']}, "
            f"risk_amt={result['risk_amount']:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[PositionSizing] Calculation error: {e}")
        return {
            'valid': False,
            'error': f'Calculation error: {str(e)}',
            'position_size_usdt': 0,
            'margin_required': 0,
            'qty': 0,
            'risk_amount': 0,
            'sl_distance_pct': 0,
        }


def format_risk_info(balance: float, risk_pct: float) -> str:
    """
    Format risk information for display to user.
    
    Args:
        balance: Current balance
        risk_pct: Risk percentage
    
    Returns:
        Formatted string with risk info
    """
    risk_amount = balance * (risk_pct / 100.0)
    
    # Calculate survivability (how many consecutive losses before account blown)
    survivability = int(100 / risk_pct)
    
    # Determine risk level
    if risk_pct <= 1.0:
        level = "Conservative"
        emoji = "🛡️"
    elif risk_pct <= 2.0:
        level = "Moderate"
        emoji = "⚖️"
    elif risk_pct <= 3.0:
        level = "Aggressive"
        emoji = "⚡"
    else:
        level = "Very Aggressive"
        emoji = "🔥"
    
    return (
        f"{emoji} <b>{level}</b>\n"
        f"Risk per trade: <b>{risk_pct}%</b> (${risk_amount:.2f})\n"
        f"Survivability: <b>{survivability}+</b> consecutive losses\n"
    )


def get_recommended_risk(balance: float) -> float:
    """
    Get recommended risk percentage based on account size.
    
    Smaller accounts can afford higher risk for faster growth.
    Larger accounts should use lower risk for capital preservation.
    
    Args:
        balance: Account balance in USDT
    
    Returns:
        Recommended risk percentage
    """
    if balance < 50:
        return 3.0  # Small account: 3% (aggressive growth)
    elif balance < 200:
        return 2.0  # Medium account: 2% (balanced)
    elif balance < 1000:
        return 1.5  # Large account: 1.5% (conservative)
    else:
        return 1.0  # Very large account: 1% (capital preservation)
