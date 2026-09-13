# Copyright (c) 2026 ink-developer

import codecs

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder
from bytespec.errors import DecodeError, EncodeError, SchemaError
from bytespec.models import PrefixLength

from ._utils import check_available
from .map import UINT_CODEC_MAPPING


class StrCodec(ICodec[str]):
    """Text prefixed with the length in encoded bytes, not characters.

    Args:
        prefix_length: Prefix size: 1, 2, 4, or 8 bytes, or ``VarUInt``. Defaults to 4 bytes.
        encoding: Python encoding, UTF-8 by default.

    Raises:
        SchemaError: Unsupported prefix or unknown encoding.
    """

    def __init__(self, prefix_length: PrefixLength = 4, encoding: str = "utf-8") -> None:
        self.prefix_length = prefix_length
        self.encoding = encoding

        try:
            codecs.lookup(encoding)
        except LookupError as exc:
            raise SchemaError(f"StrCodec: invalid encoding {encoding!r}") from exc

        codec = UINT_CODEC_MAPPING.get(prefix_length)
        if codec is None:
            raise SchemaError(f"StrCodec: invalid length prefix {prefix_length!r}")

        self.codec = codec

        super().__init__()

    @override
    def encode(self, value: str, byte_order: ByteOrder) -> bytes:
        """Encode text and prefix it with its byte length.

        Raises:
            EncodeError: The text cannot be represented in the encoding, or its length does not fit
                in the prefix.
            SchemaError: The selected Python codec is not a text encoding.
        """
        try:
            encoded = value.encode(self.encoding)
        except UnicodeError as exc:
            raise EncodeError(f"StrCodec ({self.encoding}): cannot encode {value!r}") from exc
        except LookupError as exc:
            raise SchemaError(f"StrCodec: invalid text encoding {self.encoding!r}") from exc
        return self.codec.encode(len(encoded), byte_order) + encoded

    @override
    def decode(
        self,
        buffer: bytes,
        byte_order: ByteOrder,
        offset: int,
    ) -> tuple[str, int]:
        """Read a string and return it with its absolute end offset.

        Raises:
            DecodeError: There are not enough bytes, or the prefix or text is invalid.
            SchemaError: The selected Python codec is not a text encoding.
            ValueError: Negative offset.
        """
        length, start = self.codec.decode(buffer, byte_order, offset)
        end = start + length

        check_available(buffer, start, length, codec=type(self).__name__)

        try:
            value = buffer[start:end].decode(self.encoding)
        except UnicodeError as exc:
            raise DecodeError(
                f"StrCodec ({self.encoding}) at offset {start}: invalid string bytes"
            ) from exc
        except LookupError as exc:
            raise SchemaError(f"StrCodec: invalid text encoding {self.encoding!r}") from exc
        return value, end
