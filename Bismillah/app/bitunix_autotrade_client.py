"""
Bitunix Auto Trade Client
Real trading client for Bitunix exchange integration
Signature: double SHA256 (not HMAC)
"""

import hashlib
import time
import uuid
import requests
import os
from typing import Dict, Optional, List
from datetime import datetime


class BitunixAutoTradeClient:
    def __init__(self, api_key: str = None, api_secret: str = None):
        # Jika api_key/api_secret diberikan secara eksplisit, SELALU pakai itu.
        # Fallback ke env var HANYA jika tidak ada sama sekali (untuk testing CLI).
        self.api_key = api_key if api_key else os.getenv('BITUNIX_API_KEY')
        self.api_secret = api_secret if api_secret else os.getenv('BITUNIX_API_SECRET')
        # Gateway via custom domain (lebih reliable dari *.workers.dev)
        # Set BITUNIX_GATEWAY_URL=https://proxy.cryptomentor.site di Railway Variables
        gateway = os.getenv('BITUNIX_GATEWAY_URL', '').rstrip('/')
        self.base_url = gateway if gateway else os.getenv('BITUNIX_BASE_URL', 'https://fapi.bitunix.com')

        if not self.api_key or not self.api_secret:
            print("⚠️ Bitunix API credentials not configured")

    # ------------------------------------------------------------------ #
    #  Signature helpers                                                   #
    # ------------------------------------------------------------------ #

    def _sha256(self, s: str) -> str:
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    def _make_sign(self, nonce: str, timestamp: str,
                   query_params: str = "", body: str = "") -> str:
        """
        Bitunix double-SHA256:
          digest = SHA256(nonce + timestamp + api_key + queryParams + body)
          sign   = SHA256(digest + secretKey)
        queryParams: all GET params sorted ascending by key, concatenated as key+value (no & or =)
        """
        digest = self._sha256(nonce + timestamp + self.api_key + query_params + body)
        return self._sha256(digest + self.api_secret)

    def _build_query_string(self, params: Dict) -> str:
        """Sort params by key ascending, concat as key+value (Bitunix format)."""
        return "".join(f"{k}{v}" for k, v in sorted(params.items()))

    def _auth_headers(self, query_params: str = "", body: str = "") -> Dict:
        nonce = uuid.uuid4().hex  # 32-char random
        timestamp = str(int(time.time() * 1000))
        sign = self._make_sign(nonce, timestamp, query_params, body)
        return {
            "api-key": self.api_key,
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": sign,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    # ------------------------------------------------------------------ #
    #  Core request                                                        #
    # ------------------------------------------------------------------ #

    def _request(self, method: str, endpoint: str,
                 params: Dict = None, body: Dict = None,
                 signed: bool = False, _retry: int = 0) -> Dict:
        if signed and (not self.api_key or not self.api_secret):
            return {'success': False, 'error': 'API credentials not configured'}

        url = f"{self.base_url}{endpoint}"
        params = params or {}
        body_str = ""

        if signed:
            query_str = self._build_query_string(params)
            if body:
                import json
                body_str = json.dumps(body, separators=(',', ':'))
            headers = self._auth_headers(query_str, body_str)
        else:
            headers = {"Content-Type": "application/json"}

        # Proxy rotation — PROXY_URL bisa berisi satu atau beberapa URL dipisah koma
        # Contoh: http://user:pass@ip1:port,http://user:pass@ip2:port
        import re, random
        proxy_raw = os.getenv('PROXY_URL', '')
        proxy_list = [p.strip() for p in proxy_raw.split(',') if p.strip()]
        proxy_url = random.choice(proxy_list) if proxy_list else None
        if proxy_url:
            safe_proxy = re.sub(r':[^:@]+@', ':***@', proxy_url)
            print(f"[Bitunix] Using proxy: {safe_proxy}")

        r = None
        last_error = None

        # Strategy: curl_cffi dengan browser impersonation + proxy (paling reliable)
        try:
            from curl_cffi import requests as cffi_requests
            import curl_cffi
            print(f"[Bitunix] curl_cffi version: {curl_cffi.__version__}")
            kwargs = dict(params=params, headers=headers, timeout=15, impersonate="chrome124")
            if proxy_url:
                kwargs['proxies'] = {'http': proxy_url, 'https': proxy_url}
            if method.upper() == 'GET':
                r = cffi_requests.get(url, **kwargs)
            else:
                r = cffi_requests.post(url, data=body_str, **kwargs)
            print(f"[Bitunix] curl_cffi response: {r.status_code}, html={('<html' in r.text[:100].lower())}")
            if r.status_code == 403 and '<html' in r.text[:100].lower():
                print(f"[Bitunix] curl_cffi got HTML 403")
                r = None
        except ImportError:
            pass
        except Exception as e:
            last_error = e
            print(f"[Bitunix] curl_cffi failed: {e}")
            r = None

        # Fallback: requests biasa
        if r is None:
            try:
                kwargs = dict(params=params, headers=headers, timeout=15)
                if proxy_url:
                    kwargs['proxies'] = {'http': proxy_url, 'https': proxy_url}
                if method.upper() == 'GET':
                    r = requests.get(url, **kwargs)
                else:
                    r = requests.post(url, data=body_str, **kwargs)
            except Exception as e:
                last_error = e
                r = None

        if r is None:
            return {'success': False, 'error': f'Request failed: {last_error}'}

        try:
            if r.status_code == 403:
                body_text = r.text[:200]
                print(f"[Bitunix] 403 Forbidden: {body_text[:100]}")
                # 403 dengan HTML = IP diblokir Bitunix, bukan auth error
                if '<html' in body_text.lower() or '<!doctype' in body_text.lower():
                    return {'success': False, 'error': 'IP_BLOCKED: IP server diblokir Bitunix. Pastikan PROXY_URL di-set di Railway Variables.'}
                return {'success': False, 'error': 'HTTP 403: Akses ditolak Bitunix.'}
            if r.status_code in (500, 502, 503, 504) and _retry < 2:
                # Server error — retry sekali lagi dengan delay
                import time as _time
                _time.sleep(3 * (_retry + 1))
                return self._request(method, endpoint, params, body, signed, _retry + 1)
            if r.status_code == 200:
                data = r.json()
                code = data.get('code')
                print(f"[Bitunix] {method} {endpoint} => code={code} msg={data.get('msg')}")
                if code == 0:
                    return {'success': True, 'data': data.get('data')}
                elif code == 10003:
                    # TOKEN_INVALID — bisa transient (timestamp drift), retry sekali dengan nonce baru
                    if _retry < 1 and signed:
                        import time as _time
                        _time.sleep(2)
                        return self._request(method, endpoint, params, body, signed, _retry + 1)
                    return {'success': False, 'error': 'TOKEN_INVALID: API Key/Secret salah atau IP server tidak diizinkan di Bitunix.'}
                elif code == 10007:
                    if _retry < 1 and signed:
                        import time as _time
                        _time.sleep(2)
                        return self._request(method, endpoint, params, body, signed, _retry + 1)
                    return {'success': False, 'error': 'SIGNATURE_ERROR: Signature tidak valid.'}
                else:
                    return {'success': False, 'error': f"API error {code}: {data.get('msg')}"}
            else:
                print(f"[Bitunix] HTTP {r.status_code}: {r.text[:200]}")
                return {'success': False, 'error': f'HTTP {r.status_code}: {r.text[:200]}'}
        except Exception as e:
            return {'success': False, 'error': f'Request failed: {str(e)}'}

    # ------------------------------------------------------------------ #
    #  Public endpoints                                                    #
    # ------------------------------------------------------------------ #

    def check_connection(self) -> Dict:
        """Test connectivity — public ticker + private account."""
        # Test public
        pub = self._request('GET', '/api/v1/futures/market/tickers',
                            params={'symbols': 'BTCUSDT'})
        if not pub['success']:
            return {'online': False, 'error': f"Public endpoint gagal: {pub['error']}"}

        # Test private (butuh valid API key)
        if self.api_key and self.api_secret:
            priv = self._request('GET', '/api/v1/futures/account',
                                 params={'marginCoin': 'USDT'}, signed=True)
            if not priv['success']:
                return {'online': False, 'error': priv['error']}

        return {'online': True, 'message': 'Connected to Bitunix successfully',
                'data': pub['data']}

    def get_symbol_price(self, symbol: str) -> Dict:
        result = self._request('GET', '/api/v1/futures/market/tickers',
                               params={'symbols': symbol})
        if result['success']:
            tickers = result['data']
            if tickers:
                return {'success': True, 'symbol': symbol,
                        'price': float(tickers[0].get('lastPrice', 0))}
        return result

    def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker data including mark price (used for SL validation).
        Returns: {'success': bool, 'mark_price': float, 'last_price': float}
        """
        result = self._request('GET', '/api/v1/futures/market/tickers',
                               params={'symbols': symbol})
        if result['success']:
            tickers = result['data']
            if tickers:
                ticker = tickers[0]
                return {
                    'success': True,
                    'symbol': symbol,
                    'mark_price': float(ticker.get('markPrice', ticker.get('lastPrice', 0))),
                    'last_price': float(ticker.get('lastPrice', 0)),
                }
        return result

    # ------------------------------------------------------------------ #
    #  Private endpoints                                                   #
    # ------------------------------------------------------------------ #

    def get_account_info(self) -> Dict:
        """Get USDT futures account balance."""
        result = self._request('GET', '/api/v1/futures/account',
                               params={'marginCoin': 'USDT'}, signed=True)
        if result['success']:
            d = result['data']
            return {
                'success': True,
                'available': float(d.get('available', 0)),
                'frozen': float(d.get('frozen', 0)),
                'margin': float(d.get('margin', 0)),
                'bonus': float(d.get('bonus', 0)),
                'cross_unrealized_pnl': float(d.get('crossUnrealizedPNL', 0)),
                'isolation_unrealized_pnl': float(d.get('isolationUnrealizedPNL', 0)),
                'position_mode': d.get('positionMode'),
                # legacy compat
                'balance': float(d.get('available', 0)),
                'total_unrealized_pnl': float(d.get('crossUnrealizedPNL', 0)) +
                                        float(d.get('isolationUnrealizedPNL', 0)),
            }
        return result
    
    def get_balance(self) -> Dict:
        """
        Get account balance (wrapper for get_account_info for compatibility).
        Returns available balance in USDT.
        """
        account_info = self.get_account_info()
        if account_info.get('success'):
            return {
                'success': True,
                'balance': account_info.get('available', 0),
                'available': account_info.get('available', 0),
                'total_unrealized_pnl': account_info.get('total_unrealized_pnl', 0),
            }
        return account_info

    def get_positions(self) -> Dict:
        """Get current open positions."""
        result = self._request('GET', '/api/v1/futures/position/get_pending_positions',
                               signed=True)
        if result['success']:
            raw = result['data'] or []
            positions = []
            for pos in raw:
                qty = float(pos.get('qty', 0))
                if qty == 0:
                    continue

                # Bitunix uses 'avgOpenPrice' for entry price (not 'openPrice')
                entry_price = float(pos.get('avgOpenPrice') or pos.get('openPrice') or 0)

                # TP/SL not returned by get_pending_positions — fetch from open orders if needed
                tp_price = float(pos.get('tpPrice') or pos.get('takeProfitPrice') or 0)
                sl_price = float(pos.get('slPrice') or pos.get('stopLossPrice') or 0)

                positions.append({
                    'symbol': pos.get('symbol'),
                    'side': pos.get('side', '').upper(),
                    'size': qty,
                    'entry_price': entry_price,
                    'mark_price': float(pos.get('markPrice') or pos.get('avgOpenPrice') or entry_price),
                    'pnl': float(pos.get('unrealizedPNL', 0)),
                    'leverage': pos.get('leverage'),
                    'margin_mode': pos.get('marginMode'),
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'liq_price': float(pos.get('liqPrice') or 0),
                    'realized_pnl': float(pos.get('realizedPNL') or 0),
                })
            return {'success': True, 'positions': positions,
                    'total_positions': len(positions)}
        return result

    def place_order(self, symbol: str, side: str, qty: float,
                    order_type: str = 'market', price: float = None,
                    reduce_only: bool = False) -> Dict:
        """
        Place a futures order.
        side: BUY / SELL
        order_type: market / limit
        """
        body = {
            'symbol': symbol,
            'qty': str(qty),
            'side': side.upper(),
            'tradeSide': 'OPEN' if not reduce_only else 'CLOSE',
            'orderType': order_type.upper(),
        }
        if order_type.lower() == 'limit' and price:
            body['price'] = str(price)

        result = self._request('POST', '/api/v1/futures/trade/place_order',
                               body=body, signed=True)
        if result['success']:
            return {'success': True, 'order_id': result['data'].get('orderId'),
                    'message': f'{side.upper()} {order_type} order placed'}
        return result

    # ------------------------------------------------------------------ #
    #  High-level helpers (used by handlers)                              #
    # ------------------------------------------------------------------ #

    def set_leverage(self, symbol: str, leverage: int, margin_mode: str = "cross") -> Dict:
        """Set leverage for a symbol. margin_mode: cross / isolated"""
        body = {
            "symbol": symbol,
            "leverage": str(leverage),
            "marginMode": margin_mode.upper(),
        }
        result = self._request('POST', '/api/v1/futures/account/change_leverage',
                               body=body, signed=True)
        if result['success']:
            return {'success': True, 'leverage': leverage, 'margin_mode': margin_mode}
        return result

    def place_order_with_tpsl(self, symbol: str, side: str, qty: float,
                               tp_price: float, sl_price: float) -> Dict:
        """Place market order with TP and SL attached."""
        body = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side.upper(),          # BUY / SELL
            "tradeSide": "OPEN",
            "orderType": "MARKET",
            "tpPrice": str(round(tp_price, 6)),
            "slPrice": str(round(sl_price, 6)),
            "tpStopType": "MARK_PRICE",
            "slStopType": "MARK_PRICE",
        }
        result = self._request('POST', '/api/v1/futures/trade/place_order',
                               body=body, signed=True)
        if result['success']:
            return {
                'success': True,
                'order_id': result['data'].get('orderId'),
                'symbol': symbol,
                'side': side,
                'qty': qty,
                'tp': tp_price,
                'sl': sl_price,
            }
        return result

    def set_position_sl(self, symbol: str, sl_price: float) -> Dict:
        """
        Update SL on an open position (used for breakeven after TP1 hit).
        Bitunix endpoint: POST /api/v1/futures/position/set_tpsl
        """
        body = {
            "symbol": symbol,
            "slPrice": str(round(sl_price, 6)),
            "slStopType": "MARK_PRICE",
        }
        result = self._request('POST', '/api/v1/futures/position/set_tpsl',
                               body=body, signed=True)
        if result['success']:
            return {'success': True, 'symbol': symbol, 'new_sl': sl_price}
        return result

    def close_partial(self, symbol: str, side: str, qty: float) -> Dict:
        """
        Close a partial position (reduce-only market order).
        Used to take TP1 profit on 75% of position.
        side: BUY to close SHORT, SELL to close LONG
        """
        body = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side.upper(),
            "tradeSide": "CLOSE",
            "orderType": "MARKET",
            "reduceOnly": True,
        }
        result = self._request('POST', '/api/v1/futures/trade/place_order',
                               body=body, signed=True)
        if result['success']:
            return {
                'success': True,
                'order_id': result['data'].get('orderId'),
                'symbol': symbol,
                'closed_qty': qty,
            }
        return result

    def get_24h_stats(self) -> Dict:
        return {
            'success': True,
            'stats': {
                'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
                'win_rate': 0, 'total_pnl': 0, 'best_trade': 0,
                'worst_trade': 0, 'volume_24h': 0,
            }
        }

    def start_autotrade(self, user_id: int, amount: float, wallet_address: str) -> Dict:
        account = self.get_account_info()
        if not account['success']:
            return {'success': False, 'error': f"Cannot access account: {account['error']}"}
        if account['balance'] < amount:
            return {'success': False,
                    'error': f"Insufficient balance. Available: {account['balance']} USDT, Required: {amount} USDT"}
        return {
            'success': True,
            'response': (
                f"🤖 Auto Trading Started!\n\n"
                f"💰 Allocated: {amount} USDT\n"
                f"📊 Available: {account['balance']} USDT\n"
                f"🎯 Strategy: Conservative Scalping\n"
                f"⚠️ Risk: Max 2% per trade\n"
                f"⚡ Status: ACTIVE"
            )
        }

    def get_autotrade_status(self, user_id: int) -> Dict:
        account = self.get_account_info()
        positions = self.get_positions()
        stats = self.get_24h_stats()

        if not account['success']:
            return account

        lines = [
            "📊 Auto Trade Portfolio Status\n",
            f"💰 Available: {account['balance']:.2f} USDT",
            f"📈 Unrealized PnL: {account['total_unrealized_pnl']:.2f} USDT",
            f"🔄 Open Positions: {positions.get('total_positions', 0)}",
            f"\n📊 24h Stats:",
            f"• Trades: {stats['stats']['total_trades']}",
            f"• Win Rate: {stats['stats']['win_rate']:.1f}%",
            f"• PnL: {stats['stats']['total_pnl']:.2f} USDT",
            f"\n⚡ Last Update: {datetime.now().strftime('%H:%M:%S')}",
            "\n🔄 Positions:",
        ]

        if positions['success'] and positions['positions']:
            for p in positions['positions']:
                emoji = "📈" if p['pnl'] >= 0 else "📉"
                lines.append(
                    f"{emoji} {p['symbol']} {p['side']} | "
                    f"Size: {p['size']} | Entry: ${p['entry_price']:.4f} | "
                    f"PnL: {p['pnl']:.2f} USDT"
                )
        else:
            lines.append("   No open positions")

        return {'success': True, 'response': "\n".join(lines)}

    def withdraw_autotrade(self, user_id: int) -> Dict:
        account = self.get_account_info()
        if not account['success']:
            return {'success': False, 'error': 'Cannot access account'}

        balance = account['balance']
        pnl = account['total_unrealized_pnl']
        profit = max(0, pnl)
        fee = profit * 0.25
        net = balance - fee

        return {
            'success': True,
            'response': (
                f"✅ Withdrawal Processed\n\n"
                f"💰 Balance: {balance:.2f} USDT\n"
                f"📈 PnL: {pnl:.2f} USDT\n"
                f"💸 Fee (25% profit): {fee:.2f} USDT\n"
                f"💵 Net: {net:.2f} USDT"
            )
        }

    def get_trade_history(self, user_id: int, limit: int = 10) -> Dict:
        result = self._request('GET', '/api/v1/futures/trade/get_history_orders',
                               params={'pageSize': limit}, signed=True)
        if result['success']:
            orders = result['data'] or []
            if not orders:
                return {'success': True, 'response': "📈 No trade history yet."}
            lines = [f"📈 Trade History (last {limit})\n"]
            for o in orders[:limit]:
                side_emoji = "🟢" if o.get('side') == 'BUY' else "🔴"
                lines.append(
                    f"{side_emoji} {o.get('symbol')} {o.get('side')} "
                    f"qty={o.get('qty')} @ {o.get('price', 'market')} "
                    f"| {o.get('ctime', '')}"
                )
            return {'success': True, 'response': "\n".join(lines)}
        return {'success': False, 'response': f"Failed to fetch history: {result['error']}"}


# ------------------------------------------------------------------ #
#  Quick test                                                          #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    client = BitunixAutoTradeClient()

    print("1. Connection test...")
    print(client.check_connection())

    print("\n2. Account info...")
    print(client.get_account_info())

    print("\n3. Positions...")
    print(client.get_positions())
