"""
Bybit Auto Trade Client
REST V5 API — USDT Perpetual Futures
Auth: HMAC-SHA256 (api_key + timestamp + recv_window + params)
"""

import hashlib
import hmac
import time
import json
import requests
import os
from typing import Dict, Optional, List


class BybitAutoTradeClient:
    BASE_URL = "https://api.bybit.com"

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key    = api_key    or os.getenv("BYBIT_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET", "")
        self.recv_window = "5000"

        if not self.api_key or not self.api_secret:
            print("⚠️ Bybit API credentials not configured")

    # ------------------------------------------------------------------ #
    #  Auth helpers                                                        #
    # ------------------------------------------------------------------ #

    def _sign(self, timestamp: str, payload: str) -> str:
        """Bybit V5 signature: HMAC-SHA256(timestamp + api_key + recv_window + payload)"""
        raw = timestamp + self.api_key + self.recv_window + payload
        return hmac.new(self.api_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()

    def _auth_headers(self, timestamp: str, signature: str) -> Dict:
        return {
            "X-BAPI-API-KEY":     self.api_key,
            "X-BAPI-TIMESTAMP":   timestamp,
            "X-BAPI-SIGN":        signature,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type":       "application/json",
        }

    # ------------------------------------------------------------------ #
    #  Core request                                                        #
    # ------------------------------------------------------------------ #

    def _request(self, method: str, endpoint: str,
                 params: Dict = None, body: Dict = None,
                 signed: bool = False) -> Dict:
        if signed and (not self.api_key or not self.api_secret):
            return {"success": False, "error": "API credentials not configured"}

        url = f"{self.BASE_URL}{endpoint}"
        timestamp = str(int(time.time() * 1000))

        try:
            if method.upper() == "GET":
                query_str = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
                if signed:
                    sig = self._sign(timestamp, query_str)
                    headers = self._auth_headers(timestamp, sig)
                else:
                    headers = {}
                r = requests.get(url, params=params or {}, headers=headers, timeout=10)
            else:
                body_str = json.dumps(body or {}, separators=(",", ":"))
                if signed:
                    sig = self._sign(timestamp, body_str)
                    headers = self._auth_headers(timestamp, sig)
                else:
                    headers = {"Content-Type": "application/json"}
                r = requests.post(url, data=body_str, headers=headers, timeout=10)

            r.raise_for_status()
            data = r.json()

            if data.get("retCode") != 0:
                return {"success": False, "error": data.get("retMsg", "Unknown error"), "raw": data}
            return {"success": True, "data": data.get("result", {})}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Public methods                                                      #
    # ------------------------------------------------------------------ #

    def check_connection(self) -> Dict:
        """Test API connectivity."""
        r = self._request("GET", "/v5/market/time")
        return {"success": r.get("success", False)}

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current mark price for a symbol."""
        r = self._request("GET", "/v5/market/tickers",
                          params={"category": "linear", "symbol": symbol})
        if not r.get("success"):
            return r
        items = r["data"].get("list", [])
        if not items:
            return {"success": False, "error": "Symbol not found"}
        return {"success": True, "price": float(items[0].get("markPrice", 0))}

    def get_account_info(self) -> Dict:
        """Get USDT wallet balance."""
        r = self._request("GET", "/v5/account/wallet-balance",
                          params={"accountType": "UNIFIED"}, signed=True)
        if not r.get("success"):
            return r
        accounts = r["data"].get("list", [])
        for acc in accounts:
            for coin in acc.get("coin", []):
                if coin.get("coin") == "USDT":
                    available = float(coin.get("availableToWithdraw", 0))
                    equity    = float(coin.get("equity", 0))
                    upnl      = float(coin.get("unrealisedPnl", 0))
                    return {
                        "success":              True,
                        "available":            available,
                        "total_equity":         equity,
                        "total_unrealized_pnl": upnl,
                    }
        return {"success": False, "error": "USDT balance not found"}

    def get_positions(self) -> Dict:
        """Get all open positions."""
        r = self._request("GET", "/v5/position/list",
                          params={"category": "linear", "settleCoin": "USDT"}, signed=True)
        if not r.get("success"):
            return r
        positions = []
        for p in r["data"].get("list", []):
            size = float(p.get("size", 0))
            if size == 0:
                continue
            positions.append({
                "symbol":        p["symbol"],
                "side":          p["side"].upper(),
                "size":          size,
                "entry_price":   float(p.get("avgPrice", 0)),
                "unrealized_pnl": float(p.get("unrealisedPnl", 0)),
                "leverage":      int(float(p.get("leverage", 1))),
            })
        return {"success": True, "positions": positions}

    def set_leverage(self, symbol: str, leverage: int, margin_mode: str = "cross") -> Dict:
        """Set leverage and margin mode for a symbol."""
        # Set margin mode first
        margin_val = 0 if margin_mode == "cross" else 1
        self._request("POST", "/v5/position/switch-isolated",
                      body={"category": "linear", "symbol": symbol,
                            "tradeMode": margin_val,
                            "buyLeverage": str(leverage),
                            "sellLeverage": str(leverage)},
                      signed=True)
        # Set leverage
        r = self._request("POST", "/v5/position/set-leverage",
                          body={"category": "linear", "symbol": symbol,
                                "buyLeverage": str(leverage),
                                "sellLeverage": str(leverage)},
                          signed=True)
        return r

    def place_order(self, symbol: str, side: str, qty: float,
                    order_type: str = "Market", price: float = None,
                    reduce_only: bool = False) -> Dict:
        """Place a market or limit order."""
        body = {
            "category":   "linear",
            "symbol":     symbol,
            "side":       side.capitalize(),  # Buy / Sell
            "orderType":  order_type,
            "qty":        str(qty),
            "reduceOnly": reduce_only,
            "timeInForce": "GTC" if order_type == "Limit" else "IOC",
        }
        if price and order_type == "Limit":
            body["price"] = str(price)
        return self._request("POST", "/v5/order/create", body=body, signed=True)

    def place_order_with_tpsl(self, symbol: str, side: str, qty: float,
                               tp_price: float = None, sl_price: float = None) -> Dict:
        """Place market order with TP/SL."""
        body = {
            "category":  "linear",
            "symbol":    symbol,
            "side":      side.capitalize(),
            "orderType": "Market",
            "qty":       str(qty),
            "timeInForce": "IOC",
        }
        if tp_price:
            body["takeProfit"] = str(tp_price)
        if sl_price:
            body["stopLoss"] = str(sl_price)
        return self._request("POST", "/v5/order/create", body=body, signed=True)

    def set_position_sl(self, symbol: str, sl_price: float) -> Dict:
        """Update stop-loss on existing position."""
        return self._request("POST", "/v5/position/trading-stop",
                             body={"category": "linear", "symbol": symbol,
                                   "stopLoss": str(sl_price),
                                   "slTriggerBy": "MarkPrice"},
                             signed=True)

    def close_partial(self, symbol: str, side: str, qty: float) -> Dict:
        """Close part of a position (reduce-only)."""
        close_side = "Sell" if side.upper() == "BUY" else "Buy"
        return self.place_order(symbol, close_side, qty,
                                order_type="Market", reduce_only=True)

    def get_24h_stats(self) -> Dict:
        """Get 24h ticker stats for top symbols."""
        r = self._request("GET", "/v5/market/tickers",
                          params={"category": "linear"})
        if not r.get("success"):
            return r
        return {"success": True, "data": r["data"].get("list", [])}
