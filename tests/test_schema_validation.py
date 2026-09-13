from typing import Annotated

import pytest

from bytespec import ProtoModel, SchemaError, field
from bytespec.types import CodecSpec


def test_annotated_field_without_field_roundtrips():
    class Model(ProtoModel):
        value: str

    original = Model(value="hello")
    assert Model.decode(original.encode()).value == "hello"


def test_unresolved_annotation_raises_schema_error():
    with pytest.raises(SchemaError, match="cannot resolve annotations"):
        type("BadModel", (ProtoModel,), {"__annotations__": {"value": "UndefinedWireType"}})


def test_duplicate_field_index_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5101

            a: str = field(0)
            b: str = field(0)


def test_missing_field_index_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5102

            a: str = field(0)
            b: str = field(2)


def test_negative_field_index_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5103

            value: str = field(-1)


def test_duplicate_flag_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5104

            a: str | None = field(0, flag=0)
            b: str | None = field(1, flag=0)


@pytest.mark.parametrize("flag", [-1, 64, 1000])
def test_flag_out_of_range_rejected(flag: int):
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5105

            value: str | None = field(0, flag=flag)


def test_optional_field_without_flag_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5106

            value: str | None = field(0)


def test_required_field_with_flag_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5107

            value: str = field(0, flag=0)


def test_unsupported_union_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5108

            value: str | bytes = field(0)


def test_unknown_field_type_rejected():
    class UnknownType:
        pass

    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5109

            value: UnknownType = field(0)


def test_unrelated_annotated_metadata_is_ignored():
    class Model(ProtoModel):
        value: Annotated[str, object()] = field(0)

    assert Model.decode(Model(value="hello").encode()).value == "hello"


def test_conflicting_annotated_metadata_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x510B

            value: Annotated[
                str,
                CodecSpec(prefix_length=2),
                CodecSpec(prefix_length=4),
            ] = field(0)


def test_default_and_default_factory_rejected_at_class_creation():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x510C

            value: str = field(
                0,
                default="hello",
                default_factory=lambda: "world",
            )


def test_invalid_default_type_rejected_at_class_creation():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x510D

            value: str = field(0, default=123)


def test_invalid_default_factory_result_rejected_at_instance_creation():
    class BadFactoryModel(ProtoModel):
        __constructor__ = 0x510E

        value: str = field(0, default_factory=lambda: 123)

    with pytest.raises((TypeError, ValueError)):
        BadFactoryModel()


@pytest.mark.parametrize("prefix_length", [-1, 0, 3, 5, 16])
def test_invalid_prefix_length_rejected(prefix_length: int):
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x510F

            value: str = field(0, prefix_length=prefix_length)


def test_invalid_string_encoding_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5110

            value: str = field(
                0,
                encoding="__definitely_not_a_real_encoding__",
            )


def test_invalid_codec_override_rejected():
    with pytest.raises(SchemaError):

        class BadModel(ProtoModel):
            __constructor__ = 0x5111

            value: str = field(0, codec=object())


def test_default_none_is_distinct_from_missing_for_optional_field():
    class Model(ProtoModel):
        __constructor__ = 0x5112

        value: str | None = field(0, flag=0, default=None)

    assert Model().value is None


def test_default_factory_is_not_called_at_class_creation():
    calls = 0

    def factory() -> list[str]:
        nonlocal calls
        calls += 1
        return []

    class Model(ProtoModel):
        __constructor__ = 0x5113

        values: list[str] = field(0, default_factory=factory)

    assert calls == 0

    Model()
    assert calls == 1


def test_default_factory_returns_new_object_per_instance():
    class Model(ProtoModel):
        __constructor__ = 0x5114

        values: list[str] = field(0, default_factory=list)

    first = Model()
    second = Model()

    assert first.values is not second.values
