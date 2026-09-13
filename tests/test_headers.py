import pytest

from bytespec import (
    ByteOrder,
    Constructor,
    DecodeError,
    Flags,
    PayloadLength,
    ProtoModel,
    SchemaError,
    field,
)
from bytespec.types import UInt8, UInt16, VarInt, VarUInt


class Flagged(ProtoModel):
    __header__ = (Flags(1), PayloadLength(1))
    note: str | None = field(flag=0, prefix_length=1)


@pytest.mark.parametrize("header", [(), (PayloadLength(1),)])
def test_inherited_optional_requires_flags(header):
    with pytest.raises(SchemaError, match="no Flags"):
        type("WithoutFlags", (Flagged,), {"__header__": header})


@pytest.mark.parametrize("header", [(), (PayloadLength(1),)])
def test_own_optional_requires_flags(header):
    with pytest.raises(SchemaError, match="no Flags"):
        type(
            "WithoutFlags",
            (ProtoModel,),
            {
                "__header__": header,
                "__annotations__": {"note": str | None},
                "note": field(flag=0),
            },
        )


def test_subclass_rebuilds_framing_and_preserves_fields():
    class Parent(ProtoModel):
        __constructor__ = 2
        __header__ = (Constructor(1), PayloadLength(1))
        value: UInt16 = field(default=0x1234)

    class Child(Parent):
        __constructor__ = 3
        __header__ = (PayloadLength(1), Constructor(2))
        __byte_order__ = ByteOrder.LITTLE

    assert Child.__schema__ is not Parent.__schema__
    assert Child.__schema__.model is Child
    assert Child().encode() == bytes.fromhex("02 03 00 34 12")
    restored, end = Child.decode_from(b"xx" + Child().encode() + b"tail", 2)
    assert type(restored) is Child
    assert restored.value == 0x1234
    assert end == 7
    assert Parent().encode() == bytes.fromhex("02 02 12 34")
    with pytest.raises(DecodeError):
        Child.decode(bytes.fromhex("02 02 00 34 12"))


def test_subclass_preserves_optional_fields_and_factories():
    class Parent(Flagged):
        note: str | None = field(flag=0, prefix_length=1)
        values: list[UInt8] = field(default_factory=list, prefix_length=1)

    class Child(Parent):
        __header__ = (PayloadLength(1), Flags(1))

    first, second = Child(note="A"), Child()
    first.values.append(7)
    assert second.values == []
    assert Child.decode(first.encode()) == first
    assert Child.decode(second.encode()).note is None


def test_own_fields_replace_inherited_fields():
    class Required(Flagged):
        __header__ = ()
        number: UInt8

    assert Required(number=7).encode() == b"\x07"
    with pytest.raises(TypeError, match="Unknown fields"):
        Required(number=7, note="A")


@pytest.mark.parametrize(
    "header, expected",
    [
        ((), b""),
        ((Constructor(1), PayloadLength(1)), b"\x01\x00"),
    ],
)
def test_empty_models_have_their_own_schema(header, expected):
    empty = type("Empty", (ProtoModel,), {"__header__": header})
    child = type("Child", (empty,), {})
    assert child.__schema__ is not empty.__schema__
    assert child.__schema__.model is child
    assert child().encode() == expected
    assert child.decode(expected) == child()


def test_default_header_does_not_mask_custom_header():
    class Default(ProtoModel):
        pass

    class Compact(ProtoModel):
        __header__ = (PayloadLength(1),)

    class Mixed(Default, Compact):
        value: UInt8

    assert Mixed.__header__ is Compact.__header__
    assert Mixed(value=7).encode() == b"\x01\x07"


def test_diamond_reuses_header_identity_and_rebuilds_schema():
    class Left(Flagged):
        pass

    class Right(Flagged):
        pass

    class Diamond(Left, Right):
        pass

    assert Diamond.__header__ is Flagged.__header__
    assert Diamond.__schema__ is not Left.__schema__
    assert Diamond.decode(Diamond(note="A").encode()).note == "A"


def test_distinct_equivalent_headers_require_explicit_choice():
    class Left(ProtoModel):
        __header__ = (Constructor(1),)

    class Right(ProtoModel):
        __header__ = (Constructor(1),)

    with pytest.raises(SchemaError, match="conflicting inherited headers"):
        type("Conflict", (Left, Right), {})

    class Resolved(Left, Right):
        __header__ = Left.__header__

    assert Resolved.decode(b"\x01") == Resolved()


def test_inherited_flags_must_fit_new_header():
    class Wide(ProtoModel):
        note: str | None = field(flag=8)

    with pytest.raises(SchemaError, match="flag 8"):
        type("Narrow", (Wide,), {"__header__": (Flags(1),)})


@pytest.mark.parametrize("element", [Constructor, Flags, PayloadLength])
@pytest.mark.parametrize("encoding", [1, 2, 4, 8, VarUInt])
def test_unsigned_header_encodings_roundtrip(element, encoding):
    model = type(
        "Message",
        (ProtoModel,),
        {
            "__header__": (element(encoding),),
            "__annotations__": {"value": UInt8},
        },
    )
    message = model(value=7)
    assert model.decode(message.encode()) == message


@pytest.mark.parametrize("element", [Constructor, Flags, PayloadLength])
@pytest.mark.parametrize("encoding", [3, VarInt, UInt16])
def test_unsupported_header_encoding_is_rejected(element, encoding):
    with pytest.raises(SchemaError):
        element(encoding)
