# Copyright (c) 2026 ink-developer

import struct

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import DecodeError

from ._utils import check_available


class BoolCodec(ICodec[bool]):
    """A Boolean value in one byte: 0 or 1."""

    @override
    def encode(
        self,
        value: bool,
        byte_order: ByteOrder,
    ) -> bytes:
        """Write the truth value of value as 0/1 without strict type checking."""
        return struct.pack(byte_order.value + "B", 1 if value else 0)

    @override
    def decode(
        self,
        buffer: bytes,
        byte_order: ByteOrder,
        offset: int,
    ) -> tuple[bool, int]:
        """Read a bool and return it with its absolute end offset.

        Raises:
            DecodeError: The byte is missing or is neither 0 nor 1.
            ValueError: Negative offset.
        """
        check_available(buffer, offset, 1, codec=type(self).__name__)
        value = struct.unpack_from(byte_order.value + "B", buffer, offset)[0]

        if value not in (0, 1):
            raise DecodeError(f"BoolCodec at offset {offset}: invalid bool value {value}")

        return bool(value), offset + 1
