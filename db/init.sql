-- Valkyrie Eyes — PostgreSQL schema
-- All tables are append-only (INSERT only, no UPDATE/DELETE) per the infinite retention policy.

-- ── scan_log ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scan_log (
    id                BIGSERIAL    PRIMARY KEY,
    symbol            VARCHAR(20)  NOT NULL,
    timeframe         VARCHAR(5)   NOT NULL,
    price             NUMERIC(18,6),
    pattern           VARCHAR(50),
    confidence        VARCHAR(10),
    urgency           VARCHAR(10),
    overall_bias      VARCHAR(10),
    is_valid_breakout BOOLEAN,
    confluence_score  SMALLINT,
    rr_ratio          NUMERIC(8,4),
    rsi               NUMERIC(8,4),
    ema20             NUMERIC(18,6),
    ema50             NUMERIC(18,6),
    ema200            NUMERIC(18,6),
    atr               NUMERIC(18,6),
    atr_pct           NUMERIC(8,4),
    vol_ratio         NUMERIC(8,4),
    ema50_slope       NUMERIC(18,8),
    z_score           NUMERIC(8,4),
    signal            VARCHAR(20),
    pattern_changed   BOOLEAN,
    ts                TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Supports pair_ranker's window query and time-range dashboards
CREATE INDEX IF NOT EXISTS idx_scan_log_sym_tf_ts
    ON scan_log (symbol, timeframe, ts DESC);

-- ── watchlist ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS watchlist (
    id         SERIAL       PRIMARY KEY,
    symbol     VARCHAR(20)  UNIQUE NOT NULL,
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO watchlist (symbol) VALUES
    ('BTC/USDT'),
    ('ETH/USDT'),
    ('SOL/USDT'),
    ('XRP/USDT'),
    ('BNB/USDT'),
    ('ATOM/USDT'),
    ('NEAR/USDT'),
    ('DOGE/USDT')
ON CONFLICT DO NOTHING;

-- ── cross_market_log ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cross_market_log (
    id             BIGSERIAL    PRIMARY KEY,
    market_regime  VARCHAR(20),
    leaders        JSONB,
    laggards       JSONB,
    synthesis      TEXT,
    ts             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cross_market_log_ts
    ON cross_market_log (ts DESC);
