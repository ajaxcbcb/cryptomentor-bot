# SMC Trading Engine

Deterministic Smart Money Concepts trading engine scaffold with:
- core market-state/liquidity/BOS/entry/confidence decisioning
- Bitunix adapter layer (scaffolded endpoints)
- scan/trade/analytics services
- FastAPI status/admin routes
- SQLite audit and analytics storage

## Quick Start
1. Copy `.env.example` to `.env` and configure values.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run API:
```bash
uvicorn app.main:app --reload --port 8000
```
4. Optional scanner-only runner:
```bash
python -m app.runner
```

## Endpoints
- `GET /health`
- `GET /pairs`
- `GET /status`
- `GET /status/{symbol}`
- `GET /trades/open`
- `GET /trades/history`
- `POST /admin/rescan` (protected when `TELEGRAM_AUTH_ENABLED=true`)

## Feature Flags
- `SMC_SHADOW_MODE=true`: decisioning runs, logs, analytics update, but execution path stays dry-run.
- `SMC_EXECUTION_ENABLED=false`: hard execution gate for cutover.

## Tests
```bash
pytest
```

## Bitunix Mapping Notes
`app/exchange/bitunix_client.py` is intentionally scaffolded with TODO markers for final endpoint/signature mapping.
No raw exchange payloads are leaked into core decision modules.
