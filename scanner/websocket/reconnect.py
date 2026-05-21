"""Phase 1I — Reconnect logic with capped exponential backoff."""
import asyncio
import logging
from typing import Callable

log = logging.getLogger(__name__)

_BASE_BACKOFF = 2
_MAX_BACKOFF = 60


async def with_reconnect(
    coro_fn: Callable,
    *args,
    max_retries: int = 0,
    **kwargs,
) -> None:
    """
    Wraps a coroutine in a reconnect loop with capped exponential backoff.
    max_retries=0 means unlimited retries. CancelledError propagates immediately.
    """
    attempt = 0
    while True:
        try:
            await coro_fn(*args, **kwargs)
            attempt = 0
        except asyncio.CancelledError:
            log.info("Reconnect loop cancelled cleanly")
            raise
        except Exception as exc:
            attempt += 1
            backoff = min(_BASE_BACKOFF ** attempt, _MAX_BACKOFF)
            log.warning(
                "Connection failed (attempt %d): %s — retrying in %ds",
                attempt, exc, backoff,
            )
            await asyncio.sleep(backoff)
            if max_retries and attempt >= max_retries:
                log.error("Max retries (%d) reached, giving up", max_retries)
                raise
