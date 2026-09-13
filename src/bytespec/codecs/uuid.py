# Copyright (c) 2026 ink-developer

from uuid import UUID

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder

from .bytes import FixedBytesCodec


class UUIDCodec(ICodec[UUID]):
    """A UUID as exactly 16 bytes from UUID.bytes, without a length prefix.

    The model's byte order does not switch this representation to bytes_le.
    """

    def __init__(self) -> None:
        self.codec = FixedBytesCodec(length=16)

    @override
    def encode(self, value: UUID, byte_order: ByteOrder) -> bytes:
        """Return the 16 bytes of value.bytes regardless of byte_order."""
        return self.codec.encode(value.bytes, byte_order)

    @override
    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int) -> tuple[UUID, int]:
        """Read a UUID and return it with the position offset + 16.

        Raises:
            DecodeError: There are not enough bytes for a UUID.
            ValueError: Negative offset.
        """
        value, offset = self.codec.decode(buffer, byte_order, offset)
        return UUID(bytes=value), offset
