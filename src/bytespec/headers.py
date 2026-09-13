from abc import ABC, abstractmethod

from typing_extensions import override

from bytespec.codecs.map import UINT_CODEC_MAPPING
from bytespec.errors import DecodeError, SchemaError
from bytespec.models import UIntEncoding
from bytespec.types import VarUInt

from .schema import HeaderDecodeContext, HeaderEncodeContext, ModelSchema


class HeaderElement(ABC):
    @abstractmethod
    def validate(self, schema: ModelSchema) -> None: ...

    @abstractmethod
    def encode(self, ctx: HeaderEncodeContext) -> bytes: ...

    @abstractmethod
    def decode(
        self,
        buffer: bytes,
        offset: int,
        ctx: HeaderDecodeContext,
    ) -> int: ...


class IntegerHeaderElement(HeaderElement):
    def __init__(self, encoding: UIntEncoding) -> None:
        self.encoding = encoding

        codec = UINT_CODEC_MAPPING.get(self.encoding)

        if not codec:
            raise SchemaError(f"Invalid encdoing for HeaderElement {type(self).__name__}")

        self.codec = codec


class Constructor(IntegerHeaderElement):
    """Model identifier from **constructor**, validated during decoding.

    Args:
        encoding: Unsigned integer width in bytes (1, 2, 4, 8) or VarUInt.

    Note:
        The int type is validated when building the schema; the value range
        is validated during encoding. Nested models skip this element.
    """

    @override
    def validate(self, schema: ModelSchema) -> None:
        if type(schema.constructor) is not int:
            raise SchemaError(f"Invalid constructor type: {type(schema.constructor).__name__}")

    @override
    def decode(self, buffer: bytes, offset: int, ctx: HeaderDecodeContext) -> int:
        if not ctx.expect_constructor:
            return offset

        value, offset = self.codec.decode(
            buffer,
            ctx.schema.byte_order,
            offset,
        )

        if value != ctx.schema.constructor:
            raise DecodeError(f"wrong constructor {value:#x}, expected {ctx.schema.constructor:#x}")

        return offset

    @override
    def encode(self, ctx: HeaderEncodeContext) -> bytes:
        if not ctx.include_constructor:
            return b""
        return self.codec.encode(ctx.schema.constructor, ctx.schema.byte_order)


class PayloadLength(IntegerHeaderElement):
    """The size of all encoded fields, excluding the entire header.

    Args:
        encoding: The unsigned integer width in bytes (1, 2, 4, 8), or VarUInt.

    Note:
        When reading, bounds the field buffer by the declared length. The position of this element
        within the header does not change the meaning of the stored number.
    """

    @override
    def validate(self, schema: ModelSchema) -> None: ...

    @override
    def decode(self, buffer: bytes, offset: int, ctx: HeaderDecodeContext) -> int:
        value, offset = self.codec.decode(buffer, ctx.schema.byte_order, offset)
        ctx.payload_length = value
        return offset

    @override
    def encode(self, ctx: HeaderEncodeContext) -> bytes:
        return self.codec.encode(ctx.payload_length, ctx.schema.byte_order)


class Flags(IntegerHeaderElement):
    """A bitmap indicating the presence of optional fields, computed from their values.

    Args:
        encoding: The unsigned integer width in bytes (1, 2, 4, 8), or VarUInt.

    Note:
        A field is present if its value is not None. Bit numbers are set using field(flag=...) and
        are limited to 0–63; with a fixed width, all used bits are checked to ensure they fit.
    """

    @override
    def validate(self, schema: ModelSchema) -> None:
        if self.encoding is VarUInt:  # pyright: ignore[reportUnnecessaryComparison] # I hate pylance. Because of difference between static analyzer and real runtime
            return

        flagged_fields = [field for field in schema.fields if field.flag is not None]

        if not flagged_fields:
            return

        max_flag = max(field.flag for field in flagged_fields if field.flag is not None)
        required_bits = max_flag + 1
        available_bits = self.encoding * 8

        if required_bits > available_bits:
            raise SchemaError(
                f"Flags encoding provides {available_bits} bits, model has field with flag {max_flag}"
            )

    @override
    def decode(self, buffer: bytes, offset: int, ctx: HeaderDecodeContext) -> int:
        value, offset = self.codec.decode(buffer, ctx.schema.byte_order, offset)
        ctx.flags = value
        return offset

    @override
    def encode(self, ctx: HeaderEncodeContext) -> bytes:
        return self.codec.encode(ctx.flags, ctx.schema.byte_order)
