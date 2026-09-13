# Copyright (c) 2026 ink-developer

from typing_extensions import override

from bytespec.enums import ByteOrder
from bytespec.errors import DecodeError, EncodeError

from ._utils import check_available
from .base import ICodec


class VarUIntCodec(ICodec[int]):
    """Canonical unsigned varint: 0 .. 2**64 - 1, 1 to 10 bytes.

    Groups of 7 bits are written starting with the least significant. The model's byte order does
    not affect this representation.
    """

    @override
    def encode(self, value: int, _: ByteOrder) -> bytes:
        """Write a nonnegative integer in canonical varint form.

        Raises:
            EncodeError: The value is outside the UInt64 range.
        """
        if value < 0:
            raise EncodeError(f"VarUIntCodec cannot encode negative value {value}")

        if value > 2**64 - 1:
            raise EncodeError(f"VarUIntCodec overflow: {value}")

        result = bytearray()

        while True:
            byte = value & 0x7F
            value >>= 7

            if value:
                byte |= 0x80

            result.append(byte)

            if not value:
                break

        return bytes(result)

    @override
    def decode(self, buffer: bytes, _: ByteOrder, offset: int) -> tuple[int, int]:
        """Read a varint and return the number with its absolute end offset.

        Raises:
            DecodeError: The varint is truncated, overflows, or is not in canonical form.
            ValueError: Negative offset.
        """
        value = 0
        count = 0
        shift = 0

        while True:
            check_available(buffer, offset, 1, codec=type(self).__name__)

            byte = buffer[offset]
            offset += 1
            count += 1

            if count == 10:
                if byte & 0x80:
                    raise DecodeError(f"VarUIntCodec at offset {offset - 1}: varint is too long")

                if byte & 0x7F > 1:
                    raise DecodeError(
                        f"VarUIntCodec at offset {offset - 1}: overflow byte {byte:#x}"
                    )

            data = byte & 0x7F
            value |= data << shift

            if not byte & 0x80:
                if count > 1 and data == 0:
                    raise DecodeError(f"VarUIntCodec at offset {offset - 1}: non-canonical varint")

                break

            shift += 7

        return value, offset


class VarIntCodec(VarUIntCodec):
    """Signed varint: ZigZag + unsigned varint in the Int64 range.

    Uses 1–10 bytes regardless of the model's byte order.
    """

    @override
    def encode(self, value: int, _: ByteOrder) -> bytes:
        """Apply ZigZag and write the integer as an unsigned varint.

        Raises:
            EncodeError: The value is outside the range -2**63 .. 2**63 - 1.
        """
        if value >= 0:
            value *= 2
        else:
            value = abs(value) * 2 - 1

        return super().encode(value, _)

    @override
    def decode(self, buffer: bytes, _: ByteOrder, offset: int) -> tuple[int, int]:
        """Read a ZigZag varint and return the number with its absolute end offset.

        Raises:
            DecodeError: The varint is truncated, overflows, or is not in canonical form.
            ValueError: Negative offset.
        """
        encoded, offset = super().decode(buffer, _, offset)

        value = encoded // 2 if encoded & 1 == 0 else -(encoded // 2) - 1

        return value, offset
