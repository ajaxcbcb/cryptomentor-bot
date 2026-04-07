"""
BingX Auto Trade Client
Perpetual Futures trading via BingX REST API v3
Signature: HMAC SHA256 (query string + body)
Docs: https://bingx-api.github.io/docs/
"""

import hashlib
import hmac
import time
import requests
import json
import os
from typing import Dict, Optional
from urllib.parse import urlencode


class BingXAutoTradeClient:
    BASE_URL = "https://open-api.bingx.com"

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key    = api_key    or os.getenv("BINGX_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINGX_API_SECRET", "")
        if not self.api_key or not self.api_secret:
            print("⚠️ BingX API credentials not configured")

    # ------------------------------------------------------------------ #
    #  Signature                                                           #
    # ------------------------------------------------------------------ #

    def _sign(self, params: dict) -> str:
        """HMAC-SHA256 over sorted query string."""
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _auth_params(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)
        return params

    def _headers(self) -> dict:
        return {
            "X-BX-APIKEY": self.api_key,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------ #
    #  Core request                                                        #
    # ------------------------------------------------------------------ #

    def _request(self, method: str, path: str,
                 params: dict = None, signed: bool = False) -> Dict:
        if signed and (not self.api_key or not self.api_secret):
            return {"success": False, "error": "API credentials not configured"}

        params = params or {}
        if signed:
            params = self._auth_params(params)

        url = self.BASE_URL + path
        try:
            if method.upper() == "GET":
                r = requests.get(url, params=params, headers=self._headers(), timeout=15)
            else:
                # POST: params as query string, body empty (BingX v3 style)
                r = requests.post(url, params=params, headers=self._headers(), timeout=15)

            data = r.json()
            code = data.get("code", -1)
            print(f"[BingX] {method} {path} => code={code} msg={data.get('msg', '')}")

            if code == 0:
                return {"success": True, "data": data.get("data")}
            else:
                return {"success": False, "error": f"API error {code}: {data.get('msg', '')}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Public                                                              #
    # ------------------------------------------------------------------ #

    def check_connection(self) -> Dict:
        """Test public + private connectivity."""
        pub = self._request("GET", "/openApi/swap/v2/quote/price",
                            params={"symbol": "BTC-USDT"})
        if not pub["success"]:
            return {"online": False, "error": f"Public endpoint failed: {pub['error']}"}

        if self.api_key and self.api_secret:
            priv = self.get_account_info()
            if not priv["success"]:
                return {"online": False, "error": priv["error"]}

        return {"online": True, "success": True, "message": "Connected to BingX successfully"}

    def get_symbol_price(self, symbol: str) -> Dict:
        """Get latest mark price for a symbol. symbol format: BTC-USDT"""
        sym = self._normalize_symbol(symbol)
        res = self._request("GET", "/openApi/swap/v2/quote/price",
                            params={"symbol": sym})
        if res["success"]:
            price = float(res["data"].get("price", 0))
            return {"success": True, "price": price, "symbol": sym}
        return res

    # ------------------------------------------------------------------ #
    #  Account                                                             #
    # ------------------------------------------------------------------ #

    def get_account_info(self) -> Dict:
        """Get futures account balance."""
        res = self._request("GET", "/openApi/swap/v2/user/balance", signed=True)
        if not res["success"]:
            return res
        data = res["data"] or {}
        balance_data = data.get("balance", {})
        available = float(balance_data.get("availableMargin", 0))
        equity    = float(balance_data.get("equity", 0))
        unrealized = float(balance_data.get("unrealizedProfit", 0))
        return {
            "success":              True,
            "balance":              equity,  # Total equity (untuk konsistensi dengan Bitunix)
            "available":            available,
            "equity":               equity,
            "total_unrealized_pnl": unrealized,
            "raw":                  data,
        }

    def get_positions(self) -> Dict:
        """Get all open positions."""
        res = self._request("GET", "/openApi/swap/v2/user/positions", signed=True)
        if not res["success"]:
            return res
        positions = []
        for p in (res["data"] or []):
            qty = float(p.get("positionAmt", 0))
            if qty == 0:
                continue
            
            entry_price = float(p.get("avgPrice", 0))
            mark_price = float(p.get("markPrice", 0))
            unrealized_pnl = float(p.get("unrealizedProfit", 0))
            
            positions.append({
                "symbol":         p.get("symbol", ""),
                "side":           "BUY" if qty > 0 else "SELL",  # Konsisten dengan Bitunix (BUY/SELL)
                "size":           abs(qty),
                "entry_price":    entry_price,
                "mark_price":     mark_price,
                "pnl":            unrealized_pnl,  # Tambahkan field 'pnl' untuk konsistensi
                "unrealized_pnl": unrealized_pnl,
                "leverage":       int(p.get("leverage", 1)),
                "margin_mode":    p.get("marginType", "cross").lower(),
            })
        return {"success": True, "positions": positions}

    # ------------------------------------------------------------------ #
    #  Trading                                                             #
    # ------------------------------------------------------------------ #

    def set_leverage(self, symbol: str, leverage: int,
                     margin_mode: str = "cross") -> Dict:
        """Set leverage and margin mode for a symbol."""
        sym = self._normalize_symbol(symbol)
        # Set margin mode
        margin_type = "CROSSED" if margin_mode == "cross" else "ISOLATED"
        self._request("POST", "/openApi/swap/v2/trade/marginType",
                      params={"symbol": sym, "marginType": margin_type}, signed=True)
        # Set leverage
        res = self._request("POST", "/openApi/swap/v2/trade/leverage",
                            params={"symbol": sym, "side": "LONG", "leverage": leverage},
                            signed=True)
        # Also set SHORT side leverage
        self._request("POST", "/openApi/swap/v2/trade/leverage",
                      params={"symbol": sym, "side": "SHORT", "leverage": leverage},
                      signed=True)
        return res if res["success"] else {"success": True}  # non-fatal

    def place_order(self, symbol: str, side: str, qty: float,
                    order_type: str = "MARKET",
                    price: float = None,
                    reduce_only: bool = False) -> Dict:
        """
        Place a perpetual futures order.
        side: BUY or SELL
        """
        sym = self._normalize_symbol(symbol)
        params = {
            "symbol":     sym,
            "side":       side.upper(),
            "positionSide": "LONG" if side.upper() == "BUY" else "SHORT",
            "type":       order_type.upper(),
            "quantity":   qty,
        }
        if reduce_only:
            params["reduceOnly"] = "true"
            params["positionSide"] = "SHORT" if side.upper() == "BUY" else "LONG"
        if price and order_type.upper() == "LIMIT":
            params["price"] = price

        res = self._request("POST", "/openApi/swap/v2/trade/order",
                            params=params, signed=True)
        if res["success"]:
            order_data = res["data"] or {}
            return {
                "success":  True,
                "order_id": order_data.get("orderId", ""),
                "symbol":   sym,
                "side":     side,
                "qty":      qty,
            }
        return res

    def place_order_with_tpsl(self, symbol: str, side: str, qty: float,
                               tp_price: float = None,
                               sl_price: float = None) -> Dict:
        """Place market order then set TP/SL."""
        result = self.place_order(symbol, side, qty)
        if not result["success"]:
            return result

        sym = self._normalize_symbol(symbol)
        close_side = "SELL" if side.upper() == "BUY" else "BUY"
        pos_side   = "LONG" if side.upper() == "BUY" else "SHORT"

        if tp_price:
            self._request("POST", "/openApi/swap/v2/trade/order", params={
                "symbol":       sym,
                "side":         close_side,
                "positionSide": pos_side,
                "type":         "TAKE_PROFIT_MARKET",
                "quantity":     qty,
                "stopPrice":    tp_price,
                "workingType":  "MARK_PRICE",
                "reduceOnly":   "true",
            }, signed=True)

        if sl_price:
            self._request("POST", "/openApi/swap/v2/trade/order", params={
                "symbol":       sym,
                "side":         close_side,
                "positionSide": pos_side,
                "type":         "STOP_MARKET",
                "quantity":     qty,
                "stopPrice":    sl_price,
                "workingType":  "MARK_PRICE",
                "reduceOnly":   "true",
            }, signed=True)

        return result

    def close_partial(self, symbol: str, side: str, qty: float) -> Dict:
        """Close part of a position (reduce-only)."""
        close_side = "SELL" if side.upper() == "LONG" else "BUY"
        return self.place_order(symbol, close_side, qty, reduce_only=True)

    def set_position_sl(self, symbol: str, sl_price: float) -> Dict:
        """Set stop-loss on existing position (best effort)."""
        pos_res = self.get_positions()
        if not pos_res["success"]:
            return pos_res
        sym = self._normalize_symbol(symbol)
        for p in pos_res["positions"]:
            if p["symbol"] == sym:
                close_side = "SELL" if p["side"] == "LONG" else "BUY"
                return self._request("POST", "/openApi/swap/v2/trade/order", params={
                    "symbol":       sym,
                    "side":         close_side,
                    "positionSide": p["side"],
                    "type":         "STOP_MARKET",
                    "quantity":     p["size"],
                    "stopPrice":    sl_price,
                    "workingType":  "MARK_PRICE",
                    "reduceOnly":   "true",
                }, signed=True)
        return {"success": False, "error": "Position not found"}

    def get_24h_stats(self) -> Dict:
        """Get 24h ticker stats for major pairs."""
        res = self._request("GET", "/openApi/swap/v2/quote/ticker")
        if not res["success"]:
            return res
        tickers = []
        for t in (res["data"] or []):
            tickers.append({
                "symbol":        t.get("symbol", ""),
                "last_price":    float(t.get("lastPrice", 0)),
                "price_change":  float(t.get("priceChangePercent", 0)),
                "volume":        float(t.get("volume", 0)),
            })
        return {"success": True, "tickers": tickers}

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _normalize_symbol(self, symbol: str) -> str:
        """Convert BTCUSDT → BTC-USDT for BingX format."""
        symbol = symbol.upper().replace("-", "")
        if symbol.endswith("USDT") and "-" not in symbol:
            return symbol[:-4] + "-USDT"
        return symbol
