from enum import Enum

import pytest

from bytespec import DecodeError, ProtoModel, field
from bytespec.types import Float64, UInt8, UInt32

HEADER_SIZE = 14
PAYLOAD_LENGTH_OFFSET = 10
PAYLOAD_LENGTH_SIZE = 4


def set_payload_length(buffer: bytearray, length: int) -> None:
    buffer[PAYLOAD_LENGTH_OFFSET : PAYLOAD_LENGTH_OFFSET + PAYLOAD_LENGTH_SIZE] = length.to_bytes(
        PAYLOAD_LENGTH_SIZE, "big"
    )


def payload_length(buffer: bytes | bytearray) -> int:
    return int.from_bytes(
        buffer[PAYLOAD_LENGTH_OFFSET : PAYLOAD_LENGTH_OFFSET + PAYLOAD_LENGTH_SIZE],
        "big",
    )


def assert_decode_rejected(model: type[ProtoModel], buffer: bytes | bytearray) -> None:
    with pytest.raises(DecodeError):
        model.decode(bytes(buffer))


class UInt32Message(ProtoModel):
    __constructor__ = 0x6101

    value: UInt32 = field(0)


class Float64Message(ProtoModel):
    __constructor__ = 0x6102

    value: Float64 = field(0)


class BoolMessage(ProtoModel):
    __constructor__ = 0x6103

    value: bool = field(0)


class StringMessage(ProtoModel):
    __constructor__ = 0x6104

    value: str = field(0)


class BytesMessage(ProtoModel):
    __constructor__ = 0x6105

    value: bytes = field(0)


class UInt8ListMessage(ProtoModel):
    __constructor__ = 0x6106

    values: list[UInt8] = field(0)


class UInt32ListMessage(ProtoModel):
    __constructor__ = 0x6107

    values: list[UInt32] = field(0)


class Status(str, Enum):
    OK = "ok"
    ERROR = "error"


class EnumMessage(ProtoModel):
    __constructor__ = 0x6108

    status: Status = field(0)


@pytest.mark.parametrize("size", [0, 1, 5, 13])
def test_truncated_header_rejected(size: int):
    buffer = UInt32Message(value=123).encode()

    assert_decode_rejected(UInt32Message, buffer[:size])


def test_invalid_constructor_rejected():
    buffer = bytearray(UInt32Message(value=123).encode())

    buffer[0:2] = (0xFFFF).to_bytes(2, "big")

    assert_decode_rejected(UInt32Message, buffer)


def test_payload_length_larger_than_available_buffer_rejected():
    buffer = bytearray(UInt32Message(value=123).encode())

    set_payload_length(buffer, payload_length(buffer) + 1)

    assert_decode_rejected(UInt32Message, buffer)


def test_payload_length_smaller_than_required_fields_rejected():
    buffer = bytearray(UInt32Message(value=123).encode())

    set_payload_length(buffer, payload_length(buffer) - 1)

    assert_decode_rejected(UInt32Message, buffer)


def test_trailing_garbage_rejected():
    buffer = UInt32Message(value=123).encode() + b"\xde\xad\xbe\xef"

    assert_decode_rejected(UInt32Message, buffer)


def test_truncated_uint32_rejected_even_when_header_length_matches():
    buffer = bytearray(UInt32Message(value=0x12345678).encode())

    del buffer[-1]
    set_payload_length(buffer, 3)

    assert_decode_rejected(UInt32Message, buffer)


def test_truncated_float64_rejected_even_when_header_length_matches():
    buffer = bytearray(Float64Message(value=1.25).encode())

    del buffer[-1]
    set_payload_length(buffer, payload_length(buffer) - 1)

    assert_decode_rejected(Float64Message, buffer)


def test_invalid_bool_2_rejected():
    buffer = bytearray(BoolMessage(value=True).encode())

    buffer[HEADER_SIZE] = 2

    assert_decode_rejected(BoolMessage, buffer)


def test_invalid_bool_255_rejected():
    buffer = bytearray(BoolMessage(value=True).encode())

    buffer[HEADER_SIZE] = 255

    assert_decode_rejected(BoolMessage, buffer)


def test_truncated_string_length_prefix_rejected():
    buffer = bytearray(StringMessage(value="").encode())

    # Пустая строка содержит только 4-байтовый length-prefix.
    del buffer[-1]
    set_payload_length(buffer, 3)

    assert_decode_rejected(StringMessage, buffer)


def test_declared_string_length_larger_than_remaining_payload_rejected():
    buffer = bytearray(StringMessage(value="abc").encode())

    buffer[HEADER_SIZE : HEADER_SIZE + 4] = (100).to_bytes(4, "big")

    assert_decode_rejected(StringMessage, buffer)


def test_invalid_utf8_sequence_rejected():
    buffer = bytearray(StringMessage(value="a").encode())

    # [U32 length=1][1 byte UTF-8 data]
    buffer[HEADER_SIZE + 4] = 0xFF

    assert_decode_rejected(StringMessage, buffer)


def test_truncated_bytes_length_prefix_rejected():
    buffer = bytearray(BytesMessage(value=b"").encode())

    del buffer[-1]
    set_payload_length(buffer, 3)

    assert_decode_rejected(BytesMessage, buffer)


def test_declared_bytes_length_larger_than_remaining_payload_rejected():
    buffer = bytearray(BytesMessage(value=b"abc").encode())

    buffer[HEADER_SIZE : HEADER_SIZE + 4] = (100).to_bytes(4, "big")

    assert_decode_rejected(BytesMessage, buffer)


def test_declared_list_payload_larger_than_remaining_payload_rejected():
    buffer = bytearray(UInt8ListMessage(values=[1, 2, 3]).encode())

    buffer[HEADER_SIZE : HEADER_SIZE + 4] = (100).to_bytes(4, "big")

    assert_decode_rejected(UInt8ListMessage, buffer)


def test_list_payload_that_cuts_element_in_half_rejected():
    buffer = bytearray(UInt32ListMessage(values=[0x12345678]).encode())

    # list payload = 4 bytes. Говорим, что внутри только 3,
    # хотя UInt32 нельзя декодировать из 3 байт.
    buffer[HEADER_SIZE : HEADER_SIZE + 4] = (3).to_bytes(4, "big")

    assert_decode_rejected(UInt32ListMessage, buffer)


def test_list_payload_with_truncated_prefix_rejected():
    buffer = bytearray(UInt8ListMessage(values=[]).encode())

    # У пустого списка payload состоит только из list length-prefix.
    del buffer[-1]
    set_payload_length(buffer, 3)

    assert_decode_rejected(UInt8ListMessage, buffer)


def test_invalid_enum_value_rejected():
    buffer = bytearray(EnumMessage(status=Status.OK).encode())

    # length остаётся 2, "ok" -> "xx"
    buffer[-2:] = b"xx"

    assert_decode_rejected(EnumMessage, buffer)


def test_field_cannot_read_past_declared_payload_boundary():
    buffer = bytearray(StringMessage(value="hello").encode())

    # Физически buffer полный, но header разрешает decoder'у увидеть
    # на один байт меньше. Поле не должно читать за payload boundary.
    set_payload_length(buffer, payload_length(buffer) - 1)

    assert_decode_rejected(StringMessage, buffer)


# Decode limits намеренно не тестируются здесь:
# API для max_payload_size/max_string_size/max_list_elements/max_depth
# сначала нужно зафиксировать. После этого лучше добавить отдельный
# tests/test_decode_limits.py, а не привязывать safety-тесты к временному API.
