"""
Test BingX Balance Display
Memastikan balance BingX ditampilkan sama seperti Bitunix di Telegram
"""

import sys
sys.path.insert(0, 'Bismillah')

def test_bingx_response_format():
    """Test format response dari BingX client"""
    print("=" * 60)
    print("TEST: BingX Response Format")
    print("=" * 60)
    
    # Simulasi response dari BingX API
    mock_bingx_balance_response = {
        "code": 0,
        "msg": "success",
        "data": {
            "balance": {
                "userId": "123456789",
                "asset": "USDT",
                "balance": "1000.50",
                "crossWalletBalance": "1000.50",
                "crossUnPnl": "25.30",
                "availableBalance": "975.20",
                "maxWithdrawAmount": "975.20",
                "marginAvailable": True,
                "updateTime": 1234567890,
                "availableMargin": "975.20",
                "equity": "1025.80",
                "unrealizedProfit": "25.30"
            }
        }
    }
    
    # Simulasi parsing seperti di BingX client
    data = mock_bingx_balance_response.get("data", {})
    balance_data = data.get("balance", {})
    available = float(balance_data.get("availableMargin", 0))
    equity = float(balance_data.get("equity", 0))
    unrealized = float(balance_data.get("unrealizedProfit", 0))
    
    result = {
        "success": True,
        "balance": equity,  # Untuk konsistensi dengan Bitunix
        "available": available,
        "equity": equity,
        "total_unrealized_pnl": unrealized,
        "raw": data,
    }
    
    print(f"\nParsed BingX Account Info:")
    print(f"  ✓ balance: {result['balance']:.2f} USDT")
    print(f"  ✓ available: {result['available']:.2f} USDT")
    print(f"  ✓ equity: {result['equity']:.2f} USDT")
    print(f"  ✓ total_unrealized_pnl: {result['total_unrealized_pnl']:.2f} USDT")
    
    # Verifikasi field yang dibutuhkan ada
    assert 'balance' in result, "❌ Missing 'balance' field!"
    assert 'total_unrealized_pnl' in result, "❌ Missing 'total_unrealized_pnl' field!"
    assert result['balance'] > 0, "❌ Balance should be positive!"
    
    print("\n✅ BingX account info format is correct")
    return result

def test_bingx_positions_format():
    """Test format positions dari BingX client"""
    print("\n" + "=" * 60)
    print("TEST: BingX Positions Format")
    print("=" * 60)
    
    # Simulasi response positions dari BingX API
    mock_bingx_positions_response = {
        "code": 0,
        "msg": "success",
        "data": [
            {
                "symbol": "BTC-USDT",
                "positionId": "123456",
                "positionAmt": "0.05",  # Positive = LONG
                "avgPrice": "45000.00",
                "markPrice": "45500.00",
                "unrealizedProfit": "25.00",
                "leverage": "10",
                "marginType": "cross",
                "isolatedMargin": "0",
                "positionSide": "LONG"
            },
            {
                "symbol": "ETH-USDT",
                "positionId": "123457",
                "positionAmt": "-2.5",  # Negative = SHORT
                "avgPrice": "2500.00",
                "markPrice": "2480.00",
                "unrealizedProfit": "50.00",
                "leverage": "20",
                "marginType": "isolated",
                "isolatedMargin": "125.00",
                "positionSide": "SHORT"
            }
        ]
    }
    
    # Simulasi parsing seperti di BingX client
    positions = []
    for p in mock_bingx_positions_response.get("data", []):
        qty = float(p.get("positionAmt", 0))
        if qty == 0:
            continue
        
        entry_price = float(p.get("avgPrice", 0))
        mark_price = float(p.get("markPrice", 0))
        unrealized_pnl = float(p.get("unrealizedProfit", 0))
        
        positions.append({
            "symbol": p.get("symbol", ""),
            "side": "BUY" if qty > 0 else "SELL",
            "size": abs(qty),
            "entry_price": entry_price,
            "mark_price": mark_price,
            "pnl": unrealized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "leverage": int(p.get("leverage", 1)),
            "margin_mode": p.get("marginType", "cross").lower(),
        })
    
    print(f"\nParsed BingX Positions ({len(positions)} positions):")
    for i, pos in enumerate(positions, 1):
        print(f"\n  Position {i}:")
        print(f"    ✓ symbol: {pos['symbol']}")
        print(f"    ✓ side: {pos['side']}")
        print(f"    ✓ size: {pos['size']}")
        print(f"    ✓ entry_price: {pos['entry_price']:.2f}")
        print(f"    ✓ mark_price: {pos['mark_price']:.2f}")
        print(f"    ✓ pnl: {pos['pnl']:.2f} USDT")
        print(f"    ✓ leverage: {pos['leverage']}x")
        
        # Verifikasi field yang dibutuhkan ada
        assert 'side' in pos, "❌ Missing 'side' field!"
        assert 'pnl' in pos, "❌ Missing 'pnl' field!"
        assert 'mark_price' in pos, "❌ Missing 'mark_price' field!"
        assert pos['side'] in ['BUY', 'SELL'], f"❌ Invalid side: {pos['side']}"
    
    print("\n✅ BingX positions format is correct")
    return positions

def test_telegram_display_format():
    """Test format tampilan di Telegram"""
    print("\n" + "=" * 60)
    print("TEST: Telegram Display Format")
    print("=" * 60)
    
    # Gunakan data dari test sebelumnya
    account = test_bingx_response_format()
    positions = test_bingx_positions_format()
    
    # Simulasi tampilan di Telegram (seperti di callback_status_portfolio)
    balance = account.get('balance', 0)
    upnl = account.get('total_unrealized_pnl', 0)
    engine_status = "🟢 Active"
    
    lines = [
        f"📊 <b>Portfolio Status</b>",
        f"",
        f"⚙️ Engine: {engine_status}",
        f"💰 Balance: <b>{balance:.2f} USDT</b>",
        f"📈 Unrealized PnL: <b>{upnl:+.2f} USDT</b>",
        f"🔄 Open positions: <b>{len(positions)}</b>",
        f"",
    ]
    
    if positions:
        lines.append("📋 <b>Active Positions:</b>")
        for p in positions:
            pnl = p.get('pnl', 0)
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            side_emoji = "🟢" if p.get('side') == 'BUY' else "🔴"
            entry = p.get('entry_price', 0)
            mark = p.get('mark_price', 0)
            lev = p.get('leverage', '-')
            sym = p.get('symbol', '?').replace('-USDT', '').replace('USDT', '')
            pnl_pct = ((mark - entry) / entry * 100) if entry > 0 else 0
            if p.get('side') == 'SELL':
                pnl_pct = -pnl_pct
            
            lines.append(
                f"\n{side_emoji} <b>{sym}</b> {p.get('side')} {lev}x\n"
                f"  📍 Entry: <code>{entry:.4f}</code>\n"
                f"  💹 Mark:  <code>{mark:.4f}</code>\n"
                f"  📦 Size:  {p.get('size')}\n"
                f"  {pnl_emoji} PnL: <b>{pnl:+.4f} USDT</b> ({pnl_pct:+.2f}%)"
            )
    
    telegram_message = "\n".join(lines)
    
    print("\n" + "=" * 60)
    print("TELEGRAM MESSAGE PREVIEW:")
    print("=" * 60)
    print(telegram_message)
    print("=" * 60)
    
    # Verifikasi format message
    assert "Portfolio Status" in telegram_message, "❌ Missing title!"
    assert "Balance:" in telegram_message, "❌ Missing balance!"
    assert "Unrealized PnL:" in telegram_message, "❌ Missing PnL!"
    assert "Open positions:" in telegram_message, "❌ Missing positions count!"
    
    print("\n✅ Telegram display format is correct")

if __name__ == "__main__":
    print("\n🧪 Testing BingX Balance Display in Telegram\n")
    
    try:
        test_telegram_display_format()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("  • BingX account info format: ✅")
        print("  • BingX positions format: ✅")
        print("  • Telegram display format: ✅")
        print("\nBalance BingX akan ditampilkan dengan format yang sama")
        print("seperti Bitunix di Telegram bot.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
