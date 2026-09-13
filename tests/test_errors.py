import struct
from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

import pytest

import bytespec
from bytespec import ByteOrder, DecodeError, EncodeError, Flags, ProtoModel, SchemaError, field
from bytespec.codecs import (
    BoolCodec,
    BytesCodec,
    DatetimeCodec,
    EnumCodec,
    FixedBytesCodec,
    Float32Codec,
    Float64Codec,
    Int8Codec,
    Int16Codec,
    Int32Codec,
    Int64Codec,
    ListCodec,
    StrCodec,
    UInt8Codec,
    UInt16Codec,
    UInt32Codec,
    UInt64Codec,
    UUIDCodec,
    VarIntCodec,
    VarUIntCodec,
)
from bytespec.codecs._utils import check_available
from bytespec.types import FloatSpec, IntegerSpec, UInt8, UInt32, VarInt

ORDER = ByteOrder.BIG


class Status(str, Enum):
    OK = "ok"


class Message(ProtoModel):
    value: UInt32 = field(0)


SCALARS = [
    (UInt8Codec(), 1),
    (Int8Codec(), 1),
    (UInt16Codec(), 2),
    (Int16Codec(), 2),
    (UInt32Codec(), 4),
    (Int32Codec(), 4),
    (UInt64Codec(), 8),
    (Int64Codec(), 8),
    (Float32Codec(), 4),
    (Float64Codec(), 8),
    (BoolCodec(), 1),
    (FixedBytesCodec(3), 3),
    (UUIDCodec(), 16),
]


def test_public_error_hierarchy():
    assert hasattr(bytespec, "BytespecError")
    for name in ("SchemaError", "EncodeError", "DecodeError"):
        assert issubclass(getattr(bytespec, name), bytespec.BytespecError)


@pytest.mark.parametrize("offset,size", [(-1, 0), (0, -1)])
def test_check_available_rejects_negative_api_parameters(offset, size):
    with pytest.raises(ValueError, match="must be non-negative"):
        check_available(b"abc", offset, size, codec="test")


@pytest.mark.parametrize("offset", [3, 4])
def test_check_available_allows_zero_size_at_or_past_end(offset):
    check_available(b"abc", offset, 0, codec="test")


def test_check_available_codec_name_is_keyword_only():
    with pytest.raises(TypeError):
        check_available(b"abc", 0, 1, "test")


@pytest.mark.parametrize("codec,size", SCALARS)
@pytest.mark.parametrize("order", list(ByteOrder))
def test_truncated_fixed_width_codec(codec, size, order):
    for available in range(size):
        with pytest.raises(DecodeError, match="offset"):
            codec.decode(b"xx" + b"\0" * available, order, 2)


@pytest.mark.parametrize("codec", [StrCodec(1), BytesCodec(1), ListCodec(UInt8Codec(), 1)])
def test_length_prefix_exceeds_buffer(codec):
    with pytest.raises(DecodeError, match=r"expected.*available"):
        codec.decode(b"xx\x03ab", ORDER, 2)


@pytest.mark.parametrize("codec", [StrCodec(), BytesCodec(), ListCodec(UInt8Codec())])
def test_truncated_length_prefix(codec):
    with pytest.raises(DecodeError):
        codec.decode(b"\0\0\0", ORDER, 0)


@pytest.mark.parametrize("codec", [StrCodec(1), BytesCodec(1), ListCodec(UInt8Codec(), 1)])
def test_empty_payload_prefix_past_end(codec):
    with pytest.raises(DecodeError):
        codec.decode(b"", ORDER, 1)


def test_list_item_cannot_use_bytes_after_list_payload():
    with pytest.raises(DecodeError):
        ListCodec(UInt32Codec(), 1).decode(b"\x03\0\0\0\0", ORDER, 0)


@pytest.mark.parametrize("value", [2, 255])
def test_invalid_bool(value):
    with pytest.raises(DecodeError, match=str(value)):
        BoolCodec().decode(bytes([value]), ORDER, 0)


@pytest.mark.parametrize(
    "codec,buffer,cause",
    [
        (StrCodec(1), b"\x01\xff", UnicodeDecodeError),
        (EnumCodec(Status, StrCodec(1)), b"\x02xx", ValueError),
        (DatetimeCodec(1), b"\x03bad", ValueError),
        (StrCodec(1, encoding="idna"), b"\x04xn--", UnicodeError),
        (StrCodec(1, encoding="punycode"), b"\x01\xff", UnicodeError),
        (StrCodec(1, encoding="undefined"), b"\x01a", UnicodeError),
    ],
)
def test_invalid_wire_value_preserves_cause(codec, buffer, cause):
    with pytest.raises(DecodeError, match="offset") as error:
        codec.decode(buffer, ORDER, 0)
    assert isinstance(error.value.__cause__, cause)


@pytest.mark.parametrize("codec", [VarUIntCodec(), VarIntCodec()])
@pytest.mark.parametrize("buffer", [b"", b"\x80", b"\x80\0", b"\xff" * 10, b"\xff" * 9 + b"\x02"])
def test_invalid_varints(codec, buffer):
    with pytest.raises(DecodeError):
        codec.decode(buffer, ORDER, 0)


@pytest.mark.parametrize(
    "codec,value",
    [
        (UInt8Codec(), -1),
        (UInt8Codec(), 256),
        (Int8Codec(), -129),
        (Int64Codec(), 2**63),
        (UInt64Codec(), 2**64),
        (Float32Codec(), 1e100),
        (VarUIntCodec(), -1),
        (VarUIntCodec(), 2**64),
        (VarIntCodec(), -(2**63) - 1),
        (VarIntCodec(), 2**63),
        (FixedBytesCodec(3), b"ab"),
        (StrCodec(1), "a" * 256),
        (BytesCodec(1), b"a" * 256),
        (ListCodec(UInt8Codec(), 1), [0] * 256),
    ],
)
def test_unencodable_value(codec, value):
    with pytest.raises(EncodeError):
        codec.encode(value, ORDER)


def test_numeric_encode_preserves_cause():
    with pytest.raises(EncodeError) as error:
        UInt8Codec().encode(256, ORDER)
    assert isinstance(error.value.__cause__, struct.error)


def test_string_encode_preserves_cause():
    with pytest.raises(EncodeError) as error:
        StrCodec(encoding="ascii").encode("я", ORDER)
    assert isinstance(error.value.__cause__, UnicodeEncodeError)


@pytest.mark.parametrize("encoding", ["idna", "undefined"])
def test_string_conversion_unicode_error_preserves_cause(encoding):
    with pytest.raises(EncodeError) as error:
        StrCodec(encoding=encoding).encode("a" * 64, ORDER)
    assert isinstance(error.value.__cause__, UnicodeError)


@pytest.mark.parametrize("value", [None, bytespec.core.MISSING])
def test_missing_runtime_value(value):
    model = Message(value=1)
    model.value = value
    with pytest.raises(EncodeError, match="value"):
        model.encode()


def test_deleted_required_value():
    model = Message(value=1)
    del model.value
    with pytest.raises(EncodeError, match="value"):
        model.encode()


def test_model_decode_is_bounded_before_reading_field():
    # Header permits one byte of a UInt32; three bytes belong to the next frame.
    buffer = b"\0\1" + b"\0" * 8 + b"\0\0\0\1" + b"\0\0\0\1"
    with pytest.raises(DecodeError, match=r"expected 4.*available 1"):
        Message.decode_from(buffer, 0)


def test_nested_model_cannot_read_after_parent_payload():
    class Parent(ProtoModel):
        child: Message = field(0)

    child = Message(value=1).encode()
    buffer = b"\0\1" + b"\0" * 8 + b"\0\0\0\x0f" + child
    with pytest.raises(DecodeError):
        Parent.decode_from(buffer, 0)


@pytest.mark.parametrize(
    "annotation",
    [
        list[UInt8, UInt32],
        list[UInt8 | None],
        Annotated[int, IntegerSpec(7, False)],
        Annotated[float, FloatSpec(16)],
        "UndefinedWireType",
    ],
)
def test_unsupported_schema(annotation):
    with pytest.raises(SchemaError):
        type("BadModel", (ProtoModel,), {"__annotations__": {"value": annotation}})


@pytest.mark.parametrize(
    "factory",
    [
        lambda: StrCodec(3),
        lambda: BytesCodec(VarInt),
        lambda: ListCodec(UInt8Codec(), 3),
        lambda: StrCodec(encoding="__no_such_encoding__"),
    ],
)
def test_invalid_codec_schema(factory):
    with pytest.raises(SchemaError):
        factory()


@pytest.mark.parametrize("encoding", ["rot_13", "base64_codec"])
def test_non_text_encoding_is_schema_error(encoding):
    codec = StrCodec(encoding=encoding)
    with pytest.raises(SchemaError) as error:
        codec.encode("abc", ORDER)
    assert isinstance(error.value.__cause__, LookupError)
    with pytest.raises(SchemaError) as error:
        codec.decode(b"\0\0\0\x03abc", ORDER, 0)
    assert isinstance(error.value.__cause__, LookupError)


def test_invalid_struct_format_is_schema_error():
    with pytest.raises(SchemaError) as error:
        UInt32Codec(struct_format="invalid")
    assert isinstance(error.value.__cause__, struct.error)


def test_negative_fixed_length_is_schema_error():
    with pytest.raises(SchemaError):
        FixedBytesCodec(-1)


@pytest.mark.parametrize("options", [{"index": "0"}, {"flag": "0"}])
def test_invalid_field_parameters_are_schema_errors(options):
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            first: UInt8 = field(0)
            second: UInt8 | None = field(**({"flag": 0} | options))


@pytest.mark.parametrize("value", [None, True, "1"])
def test_invalid_constructor_type_is_schema_error(value):
    with pytest.raises(SchemaError):
        type("BadModel", (ProtoModel,), {"__constructor__": value})


@pytest.mark.parametrize("value", [2**16, -1])
def test_constructor_out_of_range_is_encode_error(value):
    model = type("BadModel", (ProtoModel,), {"__constructor__": value})
    with pytest.raises(EncodeError):
        model().encode()


def test_declared_flag_must_fit_header_storage():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __header__ = (Flags(1),)
            value: UInt8 | None = field(flag=8)


def test_python_call_errors_remain_standard():
    with pytest.raises(TypeError):
        Message(unknown=1)
    with pytest.raises(TypeError):
        Message()
    with pytest.raises(TypeError):
        UInt32Codec().decode(None, ORDER, 0)


def test_custom_codec_programming_errors_are_not_wrapped():
    class BrokenCodec(UInt32Codec):
        def encode(self, value, byte_order):
            raise ValueError("implementation bug")

        def decode(self, buffer, byte_order, offset):
            raise TypeError("implementation bug")

    class BrokenModel(ProtoModel):
        value: UInt32 = field(0, codec=BrokenCodec())

    with pytest.raises(ValueError, match="implementation bug"):
        BrokenModel(value=1).encode()
    with pytest.raises(TypeError, match="implementation bug"):
        BrokenModel.decode(Message(value=1).encode())


def test_custom_bytespec_error_is_not_wrapped():
    original = DecodeError("custom failure")

    class FailedCodec(UInt32Codec):
        def decode(self, buffer, byte_order, offset):
            raise original

    class FailedModel(ProtoModel):
        value: UInt32 = field(0, codec=FailedCodec())

    with pytest.raises(DecodeError) as error:
        FailedModel.decode(Message(value=1).encode())
    assert error.value is original


@pytest.mark.parametrize(
    "codec,value",
    [
        (StrCodec(), "привет"),
        (BytesCodec(), b"abc"),
        (FixedBytesCodec(0), b""),
        (ListCodec(UInt32Codec()), [0, 2**32 - 1]),
        (EnumCodec(Status, StrCodec()), Status.OK),
        (DatetimeCodec(), datetime(2026, 9, 7)),
        (UUIDCodec(), UUID(int=42)),
        (VarUIntCodec(), 2**64 - 1),
        (VarIntCodec(), -(2**63)),
    ],
)
@pytest.mark.parametrize("order", list(ByteOrder))
def test_successful_codec_roundtrip_with_offset(codec, value, order):
    encoded = codec.encode(value, order)
    decoded, offset = codec.decode(b"xx" + encoded + b"tail", order, 2)
    assert decoded == value
    assert offset == 2 + len(encoded)
