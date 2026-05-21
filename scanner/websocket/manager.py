"""Phase 1H — WebSocket connection manager. Handles Binance combined stream lifecycle."""
import asyncio
import json
import logging
from typing import Callable

import websockets

from .reconnect import with_reconnect
from ..data.chunking import chunk_streams

log = logging.getLogger(__name__)

_BINANCE_WS_BASE = "wss://stream.binance.com:9443/stream"


class WebSocketManager:
    def __init__(
        self,
        streams: list[str],
        on_message: Callable,
        chunk_size: int = 200,
    ) -> None:
        self._streams = streams
        self._on_message = on_message
        self._chunk_size = chunk_size
        self._running = False

    async def start(self) -> None:
        self._running = True
        chunks = chunk_streams(self._streams, self._chunk_size)
        log.info(
            "WebSocketManager starting: %d streams across %d connection(s)",
            len(self._streams), len(chunks),
        )
        tasks = [
            asyncio.create_task(
                with_reconnect(self._connect_chunk, chunk, self._on_message)
            )
            for chunk in chunks
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _connect_chunk(
        self,
        streams: list[str],
        on_message: Callable,
    ) -> None:
        stream_param = "/".join(streams)
        url = f"{_BINANCE_WS_BASE}?streams={stream_param}"
        log.info("Connecting WebSocket: %d streams", len(streams))
        async with websockets.connect(url) as ws:
            log.info("WebSocket connected: %d streams", len(streams))
            async for raw in ws:
                if not self._running:
                    break
                try:
                    msg = json.loads(raw)
                    await on_message(msg)
                except Exception as exc:
                    log.error("Message handler error: %s", exc)

    async def stop(self) -> None:
        self._running = False
        log.info("WebSocket manager stopping")
