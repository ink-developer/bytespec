# Copyright (c) 2026 ink-developer

from datetime import datetime

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import DecodeError
from bytespec.models import PrefixLength

from .str import StrCodec


class DatetimeCodec(ICodec[datetime]):
    """A datetime as a length-prefixed ISO 8601 string.

    Preserves the UTC offset from isoformat(), but not the time zone name. A datetime without tzinfo
    remains naive after reading.

    Args:
        prefix_length: Prefix size: 1, 2, 4, or 8 bytes, or ``VarUInt``.
        encoding: Encoding of the ISO string, UTF-8 by default.

    Raises:
        SchemaError: Unsupported prefix or unknown encoding.
    """

    def __init__(self, prefix_length: PrefixLength = 4, encoding: str = "utf-8") -> None:
        self.codec = StrCodec(prefix_length, encoding=encoding)

    @override
    def encode(self, value: datetime, byte_order: ByteOrder) -> bytes:
        """Write value.isoformat() as a length-prefixed string.

        Raises:
            EncodeError: The string cannot be represented in the encoding, or its length does not
                fit in the prefix.
            SchemaError: The selected codec is not a text encoding.
        """
        return self.codec.encode(value.isoformat(), byte_order)

    @override
    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int) -> tuple[datetime, int]:
        """Restore a datetime and return it with its absolute end offset.

        Raises:
            DecodeError: There are not enough bytes, or the string or ISO date is invalid.
            SchemaError: The selected codec is not a text encoding.
            ValueError: Negative offset.
        """
        value, end = self.codec.decode(buffer, byte_order, offset)
        try:
            decoded = datetime.fromisoformat(value)
        except ValueError as exc:
            raise DecodeError(
                f"DatetimeCodec at offset {offset}: invalid datetime {value!r}"
            ) from exc
        return decoded, end
