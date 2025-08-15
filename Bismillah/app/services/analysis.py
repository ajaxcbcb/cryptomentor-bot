from app.utils.async_tools import gather_safe

def _structure_label(trend: str) -> str:
    """Generate structure label based on trend"""
    if not trend:
        return "Neutral"
    trend_lower = trend.lower()
    if trend_lower in ["up", "bullish", "bull"]:
        return "LONG Bias"
    elif trend_lower in ["down", "bearish", "bear"]:
        return "SHORT Bias"
    else:
        return "Neutral"

def _reason_text(trend: str, macd_hist: float) -> str:
    """Generate reason text based on indicators"""
    if not trend:
        return "Range/await momentum"

    trend_lower = trend.lower()
    if trend_lower in ["up", "bullish"] and macd_hist > 0:
        return "Trend continuation setup"
    elif trend_lower in ["down", "bearish"] and macd_hist < 0:
        return "Trend continuation setup"
    elif macd_hist > 0:
        return "Momentum building upward"
    elif macd_hist < 0:
        return "Momentum building downward"
    else:
        return "Range/await momentum"


async def analyze_coin_futures(coin: str) -> dict:
    """
    Analyze coin futures based on various indicators and market structure.

    Args:
        coin (str): The cryptocurrency symbol to analyze (e.g., "BTC").

    Returns:
        dict: A dictionary containing the analysis results, including trend,
              confidence, entry points, stop loss, take profits, and risk/reward ratio.
    """
    from app.indicators.market_structure import analyze_market_structure
    from app.indicators.momentum import analyze_momentum
    from app.indicators.price import get_current_price
    from app.indicators.trend import analyze_trend
    from app.indicators.volume import analyze_volume
    from app.providers.tradingview import TradingViewProvider

    provider = TradingViewProvider()

    # Fetch all required data concurrently
    (
        current_price,
        overall_trend,
        confidence_score,
        entry_price,
        stop_loss,
        take_profit_1,
        take_profit_2,
        risk_reward,
        market_structure,
        momentum_data,
        volume_analysis,
    ) = await gather_safe(
        get_current_price(coin),
        analyze_trend(coin),
        provider.get_confidence_score(coin),
        provider.get_entry_price(coin),
        provider.get_stop_loss(coin),
        provider.get_take_profit_1(coin),
        provider.get_take_profit_2(coin),
        provider.get_risk_reward_ratio(coin),
        analyze_market_structure(coin),
        analyze_momentum(coin),
        analyze_volume(coin),
    )

    # Check if essential data is available
    if not all(
        [
            current_price,
            overall_trend,
            confidence_score,
            entry_price,
            stop_loss,
            take_profit_1,
            take_profit_2,
            risk_reward,
            market_structure,
            momentum_data,
            volume_analysis,
        ]
    ):
        return {"symbol": coin, "success": False, "error": "Failed to fetch all required data"}

    # Add field for formatter
    structure = _structure_label(overall_trend)
    reason = _reason_text(overall_trend, momentum_data.get("macd_histogram", 0))

    # Get 24h change via Binance
    change_24h = 0.0
    try:
        from app.providers.binance import BINANCE_URL
        from app.providers.http import fetch_json
        ticker_data = await fetch_json(
            f"{BINANCE_URL}/api/v3/ticker/24hr", 
            params={"symbol": f"{coin.upper()}USDT"}, 
            cache_key=f"bn24:{coin}", 
            cache_ttl=15
        )
        change_24h = float(ticker_data.get("priceChangePercent", 0.0))
    except Exception:
        change_24h = 0.0

    # Return comprehensive analysis
    return {
        "symbol": coin,
        "coin": coin,  # alias untuk formatter
        "price": current_price,
        "trend": overall_trend,
        "confidence": confidence_score,
        "entry": entry_price,
        "stop": stop_loss,  # alias untuk formatter
        "stop_loss": stop_loss,
        "tp1": take_profit_1,
        "tp2": take_profit_2,
        "rr": risk_reward,  # alias untuk formatter
        "risk_reward_ratio": risk_reward,
        "structure": structure,
        "reason": reason,
        "change_24h": change_24h,
        "volume_trend": volume_analysis.get("trend", "normal"),
        "market_structure": market_structure,
        "support_resistance": support_resistance,
        "momentum_indicators": momentum_data,
        "success": True
    }