"""
pair_ranker.py — Ranks trading pairs by average confluence score.

Public API: get_ranked_pairs() -> list[dict]

Reads from PostgreSQL scan_log. Returns empty list on any error so the
scanner's fallback path always works without a DB seed.
"""
import logging
import os

import psycopg2

log = logging.getLogger(__name__)

_DB_CFG = dict(
    host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    dbname=os.getenv("POSTGRES_DB", "valkyrie"),
    user=os.getenv("POSTGRES_USER", "valkyrie_user"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

_RANK_SQL = """
    SELECT symbol, timeframe, AVG(confluence_score) AS avg_score
    FROM (
        SELECT symbol, timeframe, confluence_score,
               ROW_NUMBER() OVER (
                   PARTITION BY symbol, timeframe
                   ORDER BY ts DESC
               ) AS rn
        FROM scan_log
    ) sub
    WHERE rn <= 100
    GROUP BY symbol, timeframe
    ORDER BY avg_score DESC
"""


def get_ranked_pairs() -> list[dict]:
    """
    Returns [{"symbol": str, "timeframe": str, "confluence_score": float}, ...]
    sorted by avg confluence_score descending.
    Returns [] if the table is empty or unreachable.
    """
    try:
        conn = psycopg2.connect(**_DB_CFG)
        try:
            with conn.cursor() as cur:
                cur.execute(_RANK_SQL)
                rows = cur.fetchall()
        finally:
            conn.close()

        return [
            {
                "symbol": row[0],
                "timeframe": row[1],
                "confluence_score": float(row[2] or 0),
            }
            for row in rows
        ]
    except Exception as exc:
        log.warning("pair_ranker: DB query failed (%s) — returning empty ranking", exc)
        return []
