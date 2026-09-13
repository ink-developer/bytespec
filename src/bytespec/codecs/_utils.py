# Copyright (c) 2026 ink-developer

from bytespec.errors import DecodeError


def check_available(buffer: bytes, offset: int, size: int, *, codec: str) -> None:
    if offset < 0:
        raise ValueError(f"offset must be non-negative, got {offset}")
    if size < 0:
        raise ValueError(f"size must be non-negative, got {size}")

    available = max(0, len(buffer) - offset)
    if available < size:
        raise DecodeError(
            f"{codec} at offset {offset}: expected {size} bytes, available {available}"
        )
