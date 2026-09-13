# Copyright (c) 2026 ink-developer

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import EncodeError, SchemaError
from bytespec.models import PrefixLength

from ._utils import check_available
from .map import UINT_CODEC_MAPPING


class BytesCodec(ICodec[bytes]):
    """Bytes prefixed with their length.

    Args:
        prefix_length: Prefix size: 1, 2, 4, or 8 bytes, or ``VarUInt``. Defaults to 4 bytes. The
            prefix itself is not included in the stored length.

    Raises:
        SchemaError: Unsupported prefix, including ``VarInt``.
    """

    def __init__(self, prefix_length: PrefixLength = 4) -> None:
        self.prefix_length = prefix_length

        codec = UINT_CODEC_MAPPING.get(prefix_length)
        if codec is None:
            raise SchemaError(f"BytesCodec: invalid length prefix {prefix_length!r}")

        self.codec = codec

        super().__init__()

    @override
    def encode(self, value: bytes, byte_order: ByteOrder) -> bytes:
        """Write the length of value followed by the bytes themselves.

        Raises:
            EncodeError: The length does not fit in the selected prefix.
        """
        return self.codec.encode(len(value), byte_order) + value

    @override
    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int) -> tuple[bytes, int]:
        """Read the prefix and return the bytes with their absolute end offset.

        Raises:
            DecodeError: The prefix or declared data is incomplete or invalid.
            ValueError: Negative offset.
        """
        length, start = self.codec.decode(buffer, byte_order, offset)
        end = start + length

        check_available(buffer, start, length, codec=type(self).__name__)

        return buffer[start:end], end


class FixedBytesCodec(BytesCodec):
    """Exactly length bytes without a length prefix.

    Args:
        length: The nonnegative fixed size of the value.

    Raises:
        SchemaError: Negative length.
    """

    def __init__(self, length: int) -> None:
        if length < 0:
            raise SchemaError(f"FixedBytesCodec: length must be non-negative, got {length}")
        self.length = length

    @override
    def encode(self, value: bytes, byte_order: ByteOrder) -> bytes:
        """Return value after checking its length; byte order has no effect.

        Raises:
            EncodeError: The size of value is not equal to length.
        """
        if len(value) != self.length:
            raise EncodeError(f"FixedBytesCodec: expected {self.length} bytes, got {len(value)}")

        return value

    @override
    def decode(
        self,
        buffer: bytes,
        byte_order: ByteOrder,
        offset: int,
    ) -> tuple[bytes, int]:
        """Read length bytes and return them with their absolute end offset.

        Raises:
            DecodeError: There are not enough bytes.
            ValueError: Negative offset.
        """
        end = offset + self.length

        check_available(buffer, offset, self.length, codec=type(self).__name__)

        return buffer[offset:end], end
