# Copyright (c) 2026 ink-developer

import struct
from typing import Generic, TypeVar

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import EncodeError, SchemaError

from ._utils import check_available

T = TypeVar("T")


class IntegerCodec(ICodec[T], Generic[T]):
    def __init__(self, struct_format: str, length: int) -> None:
        try:
            struct.calcsize(ByteOrder.BIG.value + struct_format)
        except struct.error as exc:
            raise SchemaError(
                f"{type(self).__name__}: invalid struct format {struct_format!r}"
            ) from exc
        self.struct_format = struct_format
        self.length = length

    @override
    def encode(
        self,
        value: T,
        byte_order: ByteOrder,
    ) -> bytes:
        """Write a fixed-width number in the specified byte order.

        Raises:
            EncodeError: The value cannot be packed in the selected numeric format.
        """
        try:
            return struct.pack(byte_order.value + self.struct_format, value)
        except (struct.error, OverflowError) as exc:
            raise EncodeError(
                f"{type(self).__name__} ({self.struct_format}): cannot encode {value!r}"
            ) from exc

    @override
    def decode(
        self,
        buffer: bytes,
        byte_order: ByteOrder,
        offset: int,
    ) -> tuple[T, int]:
        """Read a number and return it with its absolute end offset.

        Raises:
            DecodeError: There are not enough bytes for the number.
            ValueError: Negative offset.
        """
        size = struct.calcsize(byte_order.value + self.struct_format)
        check_available(buffer, offset, size, codec=type(self).__name__)
        value = struct.unpack_from(byte_order.value + self.struct_format, buffer, offset)[0]
        return value, offset + self.length


class UInt8Codec(IntegerCodec[int]):
    """Unsigned 8-bit integer: 0–255, one byte by default."""

    def __init__(self, struct_format: str = "B", length: int = 1) -> None:
        super().__init__(struct_format, length)


class Int8Codec(UInt8Codec):
    """Signed 8-bit integer: -128–127, one byte by default."""

    def __init__(self, struct_format: str = "b", length: int = 1) -> None:
        super().__init__(struct_format, length)


class UInt16Codec(IntegerCodec[int]):
    """Unsigned 16-bit integer: 0–65535, two bytes by default."""

    def __init__(self, struct_format: str = "H", length: int = 2) -> None:
        super().__init__(struct_format, length)


class Int16Codec(UInt16Codec):
    """Signed 16-bit integer: -32768–32767, two bytes by default."""

    def __init__(self, struct_format: str = "h", length: int = 2) -> None:
        super().__init__(struct_format, length)


class UInt32Codec(IntegerCodec[int]):
    """Unsigned 32-bit integer: 0 .. 2**32 - 1, four bytes."""

    def __init__(self, struct_format: str = "I", length: int = 4) -> None:
        super().__init__(struct_format, length)


class Int32Codec(UInt32Codec):
    """Signed 32-bit integer: -2**31 .. 2**31 - 1, four bytes."""

    def __init__(self, struct_format: str = "i", length: int = 4) -> None:
        super().__init__(struct_format, length)


class UInt64Codec(IntegerCodec[int]):
    """Unsigned 64-bit integer: 0 .. 2**64 - 1, eight bytes."""

    def __init__(self, struct_format: str = "Q", length: int = 8) -> None:
        super().__init__(struct_format, length)


class Int64Codec(UInt64Codec):
    """Signed 64-bit integer: -2**63 .. 2**63 - 1, eight bytes."""

    def __init__(self, struct_format: str = "q", length: int = 8) -> None:
        super().__init__(struct_format, length)
