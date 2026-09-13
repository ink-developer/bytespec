# Copyright (c) 2026 ink-developer

from enum import Enum
from typing import Any

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import DecodeError


class EnumCodec(ICodec[Enum]):
    """An enum encoded using a codec for its value.

    Args:
        enum_type: The enum class used to reconstruct members via enum_type(value).
        value_codec: The codec for .value, such as StrCodec or UInt8Codec.
    """

    def __init__(
        self,
        enum_type: type[Enum],
        value_codec: ICodec[Any],
    ) -> None:
        self.enum_type = enum_type
        self.value_codec = value_codec

    @override
    def encode(self, value: Enum, byte_order: ByteOrder) -> bytes:
        """Write value.value using the selected value codec."""
        return self.value_codec.encode(value.value, byte_order)

    @override
    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int) -> tuple[Enum, int]:
        """Read an enum member and return it with its absolute end offset.

        Raises:
            DecodeError: The decoded value is not an enum member, or the value codec rejected the
                data.
        """
        value, end = self.value_codec.decode(buffer, byte_order, offset)
        try:
            decoded = self.enum_type(value)
        except ValueError as exc:
            raise DecodeError(
                f"EnumCodec ({self.enum_type.__name__}) at offset {offset}: invalid value {value!r}"
            ) from exc
        return decoded, end
