"""
Binance Futures Auto Trade Client
USDT-M Perpetual Futures (fapi.binance.com)
Auth: HMAC-SHA256 query signature
"""

import hashlib
import hmac
import time
import json
import requests
import os
from typing import Dict, Optional
from urllib.parse import urlencode


class BinanceAutoTradeClient:
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key    = api_key    or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")

        if not self.api_key or not self.api_secret:
            print("⚠️ Binance API credentials not configured")

    # ------------------------------------------------------------------ #
    #  Auth helpers                                                        #
    # ------------------------------------------------------------------ #

    def _sign(self, params: Dict) -> str:
        query = urlencode(params)
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    def _auth_headers(self) -> Dict:
        return {"X-MBX-APIKEY": self.api_key, "Content-Type": "application/json"}

    # ------------------------------------------------------------------ #
    #  Core request                                                        #
    # ------------------------------------------------------------------ #

    def _request(self, method: str, endpoint: str,
                 params: Dict = None, signed: bool = False) -> Dict:
        if signed and (not self.api_key or not self.api_secret):
            return {"success": False, "error": "API credentials not configured"}

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        try:
            headers = self._auth_headers() if signed else {}
            if method.upper() == "GET":
                r = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == "POST":
                r = requests.post(url, params=params, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                r = requests.delete(url, params=params, headers=headers, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            r.raise_for_status()
            data = r.json()

            if isinstance(data, dict) and data.get("code") and data["code"] != 200:
                return {"success": False, "error": data.get("msg", "Unknown error"), "raw": data}
            return {"success": True, "data": data}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Public methods                                                      #
    # ------------------------------------------------------------------ #

    def check_connection(self) -> Dict:
        r = self._request("GET", "/fapi/v1/ping")
        return {"success": r.get("success", False)}

    def get_symbol_price(self, symbol: str) -> Dict:
        r = self._request("GET", "/fapi/v1/premiumIndex", params={"symbol": symbol})
        if not r.get("success"):
            return r
        return {"success": True, "price": float(r["data"].get("markPrice", 0))}

    def get_account_info(self) -> Dict:
        r = self._request("GET", "/fapi/v2/account", signed=True)
        if not r.get("success"):
            return r
        data = r["data"]
        available = float(data.get("availableBalance", 0))
        equity    = float(data.get("totalWalletBalance", 0))
        upnl      = float(data.get("totalUnrealizedProfit", 0))
        return {
            "success":              True,
            "available":            available,
            "total_equity":         equity,
            "total_unrealized_pnl": upnl,
        }

    def get_positions(self) -> Dict:
        r = self._request("GET", "/fapi/v2/positionRisk", signed=True)
        if not r.get("success"):
            return r
        positions = []
        for p in r["data"]:
            size = float(p.get("positionAmt", 0))
            if size == 0:
                continue
            side = "BUY" if size > 0 else "SELL"
            positions.append({
                "symbol":         p["symbol"],
                "side":           side,
                "size":           abs(size),
                "entry_price":    float(p.get("entryPrice", 0)),
                "unrealized_pnl": float(p.get("unRealizedProfit", 0)),
                "leverage":       int(p.get("leverage", 1)),
            })
        return {"success": True, "positions": positions}

    def set_leverage(self, symbol: str, leverage: int, margin_mode: str = "cross") -> Dict:
        # Set margin type
        self._request("POST", "/fapi/v1/marginType",
                      params={"symbol": symbol,
                              "marginType": "CROSSED" if margin_mode == "cross" else "ISOLATED"},
                      signed=True)
        # Set leverage
        r = self._request("POST", "/fapi/v1/leverage",
                          params={"symbol": symbol, "leverage": leverage},
                          signed=True)
        return {"success": r.get("success", False)}

    def place_order(self, symbol: str, side: str, qty: float,
                    order_type: str = "MARKET", price: float = None,
                    reduce_only: bool = False) -> Dict:
        params = {
            "symbol":   symbol,
            "side":     side.upper(),
            "type":     order_type.upper(),
            "quantity": qty,
        }
        if reduce_only:
            params["reduceOnly"] = "true"
        if price and order_type.upper() == "LIMIT":
            params["price"]       = price
            params["timeInForce"] = "GTC"
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def place_order_with_tpsl(self, symbol: str, side: str, qty: float,
                               tp_price: float = None, sl_price: float = None) -> Dict:
        # Binance: place main order first, then separate TP/SL orders
        r = self.place_order(symbol, side, qty)
        if not r.get("success"):
            return r
        close_side = "SELL" if side.upper() == "BUY" else "BUY"
        if tp_price:
            self._request("POST", "/fapi/v1/order",
                          params={"symbol": symbol, "side": close_side,
                                  "type": "TAKE_PROFIT_MARKET",
                                  "stopPrice": tp_price, "closePosition": "true"},
                          signed=True)
        if sl_price:
            self._request("POST", "/fapi/v1/order",
                          params={"symbol": symbol, "side": close_side,
                                  "type": "STOP_MARKET",
                                  "stopPrice": sl_price, "closePosition": "true"},
                          signed=True)
        return r

    def set_position_sl(self, symbol: str, sl_price: float) -> Dict:
        # Cancel existing SL then place new one
        side_r = self.get_positions()
        close_side = "SELL"
        if side_r.get("success"):
            for p in side_r.get("positions", []):
                if p["symbol"] == symbol:
                    close_side = "SELL" if p["side"] == "BUY" else "BUY"
                    break
        return self._request("POST", "/fapi/v1/order",
                             params={"symbol": symbol, "side": close_side,
                                     "type": "STOP_MARKET",
                                     "stopPrice": sl_price, "closePosition": "true"},
                             signed=True)

    def close_partial(self, symbol: str, side: str, qty: float) -> Dict:
        close_side = "SELL" if side.upper() == "BUY" else "BUY"
        return self.place_order(symbol, close_side, qty,
                                order_type="MARKET", reduce_only=True)

    def get_24h_stats(self) -> Dict:
        r = self._request("GET", "/fapi/v1/ticker/24hr")
        if not r.get("success"):
            return r
        return {"success": True, "data": r["data"]}
