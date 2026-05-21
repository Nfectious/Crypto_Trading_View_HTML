"""Phase 1G — WebSocket stream chunking. Batches streams to respect connection limits."""
from typing import TypeVar

T = TypeVar("T")


def chunk_streams(streams: list[T], chunk_size: int) -> list[list[T]]:
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")
    return [streams[i : i + chunk_size] for i in range(0, len(streams), chunk_size)]
