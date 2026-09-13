# Copyright (c) 2026 ink-developer

from typing import Any

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import SchemaError
from bytespec.models import PrefixLength

from ._utils import check_available
from .map import UINT_CODEC_MAPPING


class ListCodec(ICodec[list[Any]]):
    """A list prefixed with the total size of its encoded items in bytes.

    Args:
        item_codec: The codec for a single item. When reading, it must advance offset by a positive
            number of bytes within the supplied buffer.
        prefix_length: Prefix size: 1, 2, 4, or 8 bytes, or ``VarUInt``. Defaults to 4 bytes. The
            prefix does not store the item count.

    Raises:
        SchemaError: Unsupported length prefix.
    """

    def __init__(self, item_codec: ICodec[Any], prefix_length: PrefixLength = 4) -> None:
        self.item_codec = item_codec
        self.prefix_length = prefix_length

        codec = UINT_CODEC_MAPPING.get(prefix_length)
        if codec is None:
            raise SchemaError(f"ListCodec: invalid length prefix {prefix_length!r}")

        self.codec = codec

    @override
    def encode(self, data: list[Any], byte_order: ByteOrder) -> bytes:
        """Write consecutive items prefixed with their total byte length.

        Raises:
            EncodeError: The size does not fit in the prefix, or an item cannot be encoded by the
                selected codec.
        """
        payload = bytearray()

        for value in data:
            payload.extend(self.item_codec.encode(value, byte_order))

        return self.codec.encode(len(payload), byte_order) + payload

    @override
    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int) -> tuple[list[Any], int]:
        """Read a list and return it with its absolute end offset.

        Items are read from a separate buffer containing the list contents; offsets in their errors
        refer to that buffer.

        Raises:
            DecodeError: The prefix or data is incomplete, or the item codec rejected the data.
            ValueError: Negative offset.
        """
        length, start = self.codec.decode(buffer, byte_order, offset)
        end = start + length

        check_available(buffer, start, length, codec=type(self).__name__)

        values = buffer[start:end]
        data = []
        item_offset = 0
        while item_offset < len(values):
            value, item_offset = self.item_codec.decode(values, byte_order, item_offset)
            data.append(value)

        return data, end
