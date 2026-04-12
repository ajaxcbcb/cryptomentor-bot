# Exchange Integration Notes (Bitunix + Data Sources)

## Scope

- Primary exchange adapter: `Bismillah/app/bitunix_autotrade_client.py`
- Client factory/registry: `Bismillah/app/exchange_registry.py`
- Web wrappers: `website-backend/app/services/bitunix.py`, routes in `website-backend/app/routes/bitunix.py`
- Market data provider fallback: `Bismillah/app/providers/alternative_klines_provider.py`

---

## 1) Exchange Adapter Structure

### `BitunixAutoTradeClient`

Responsibilities:
- Build signatures/headers for signed private endpoints.
- Execute HTTP requests with proxy and retry behavior.
- Normalize account and position payloads.
- Provide high-level methods used by engines and web services.

Auth/signing details (confirmed from code):
- Uses nonce + timestamp + API key + query/body hashing flow.
- Signed headers include `api-key`, `nonce`, `timestamp`, `sign`.

Transport behavior:
- Tries `curl_cffi` first with browser impersonation.
- Falls back to `requests`.
- Proxy rotation and penalty handling for failing proxies.

---

## 2) Public Market Data Endpoints Used

### Bitunix public (OHLCV)
- `GET /api/v1/futures/market/kline` in provider fallback chain.

### Bitunix public ticker
- `GET /api/v1/futures/market/tickers` via `get_ticker()`.

### Binance fallback
- Futures klines: `https://fapi.binance.com/fapi/v1/klines`.
- Web signal ticker path: `https://api.binance.com/api/v3/ticker/24hr`.

### Additional fallback sources
- CryptoCompare and CoinGecko (in `alternative_klines_provider`).

---

## 3) Private Trading/Account Endpoints Used

Confirmed from client code:

- Account:
  - `GET /api/v1/futures/account`

- Positions:
  - `GET /api/v1/futures/position/get_pending_positions`

- Open/pending orders:
  - `GET /api/v1/futures/trade/get_pending_orders`

- Place order:
  - `POST /api/v1/futures/trade/place_order`
  - used for market entries, attached TP/SL, and reduce-only closes.

- Change leverage:
  - `POST /api/v1/futures/account/change_leverage`

- Change margin mode:
  - `POST /api/v1/futures/account/change_margin_mode`

- Modify TP/SL on position:
  - `POST /api/v1/futures/tpsl/position/modify_order`

- History:
  - `GET /api/v1/futures/trade/get_history_orders`

---

## 4) Symbol Mapping and Normalization

Confirmed from code:
- Swing signal base symbols are normalized to `SYMBOL + "USDT"` when routed to exchange.
- `alternative_klines_provider` strips quote assets and re-appends `USDT` for futures symbol fetch.
- Web routes normalize incoming symbols by removing `/` and uppercasing.

Examples:
- `BTC` -> `BTCUSDT`
- `BTC/USDT` -> `BTCUSDT`

---

## 5) Mark Price vs Last Price Behavior

Confirmed from code:
- `get_ticker()` returns both `mark_price` and `last_price`.
- Entry validation and TP/SL trigger semantics rely primarily on mark price.
- TP/SL order fields set stop type to `MARK_PRICE`.
- Some fallback logic uses last price if mark is unavailable.

---

## 6) ETH / Bitunix-Specific Logic

ETH-specific:
- ETH is included in symbol universes and precision maps.
- No ETH-only strategy branch was found in core runtime path.

Bitunix-specific:
- Primary execution adapter and private endpoints are Bitunix oriented.
- Web API key onboarding and verification flows are centered on Bitunix account linking.
- Some route and DB naming still reference Bitunix UID verification semantics.

---

## 7) Web Backend Integration Path

Confirmed from code:
- Website backend decrypts user API keys from `user_api_keys`.
- Calls Bitunix client via async `to_thread` wrappers.
- Exposes endpoints for account, positions, trade history, TP/SL updates, and close actions.

Special handling:
- Position source labeling (`autotrade` vs `1_click`) is inferred by matching live positions to open DB trades.
- Manual close endpoint only permits source `1_click` positions.

---

## 8) Observed Integration Risks / Ambiguities

Unclear from code:
- In `website-backend/app/services/bitunix.py`, `fetch_trade_history(symbol=...)` passes symbol as first arg to client history method whose signature is `(user_id, limit=10)`. Symbol filtering intent appears mismatched.
- Multiple remotes/execution surfaces (bot + web) operate on same exchange account state; central arbitration policy is not explicit.
