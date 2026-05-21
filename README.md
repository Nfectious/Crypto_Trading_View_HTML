# Valkyrie Eyes v5.0.1

Headless cryptocurrency market scanner. Fetches OHLCV data from Binance via REST, runs a full technical indicator and signal pipeline, detects cross-market regime, and writes everything to PostgreSQL with infinite retention.

## Stack

| Component | Technology |
|---|---|
| Scanner | Python 3.11 + asyncio + ccxt |
| Database | PostgreSQL 15 |
| Container | Docker + Docker Compose |

## Quick Start

### 1. Configure environment

```bash
cp scanner/.env.example .env
# Edit .env — at minimum set POSTGRES_PASSWORD
```

### 2. Build and run

```bash
docker compose up --build
```

### 3. Verify

```bash
# Check scanner is running
docker compose logs scanner

# Check data is flowing after first scan cycle (~60s)
docker compose exec postgres psql -U valkyrie_user -d valkyrie \
  -c "SELECT count(*) FROM scan_log;"
```

## Project Structure

```
scanner/
  headless_scanner.py   main scan loop (REST polling, 60s interval)
  quant_engine.py       indicators + signal classification
  pair_ranker.py        ranks pairs by confluence for scan ordering
  config/               env parsing and typed config dataclasses
  data/                 symbol/timeframe parsers, WebSocket stream helpers, kline model
  websocket/            WS connection manager + reconnect logic (future live feed)
  cache/                rolling window cache, partial + closed candle handlers
db/
  init.sql              schema: scan_log, watchlist, cross_market_log
docker/
  Dockerfile
docker-compose.yml
```

## Environment Variables

See `scanner/.env.example` for the full list with inline documentation.

Required before first run:
- `POSTGRES_PASSWORD` — set a strong password

## Database Tables

| Table | Purpose |
|---|---|
| `scan_log` | Every scan result row — append-only, infinite retention |
| `watchlist` | Active trading pairs the scanner processes |
| `cross_market_log` | Cross-market regime computed each cycle |

## Signals

The quant engine classifies each symbol/timeframe into one of:
`bullish_breakout`, `bearish_breakdown`, `volatile_expansion`, `pullback_bull`, `pullback_bear`, `ranging`, `unclear`

Confidence is `high / medium / low` based on a 0–10 confluence score.

---

This software is for educational and engineering purposes only and is not financial advice.
