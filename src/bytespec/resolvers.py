# Copyright (c) 2026 ink-developer

from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol, TypeAlias, get_args

from bytespec.codecs import ICodec
from bytespec.errors import SchemaError

from .codecs import (
    BoolCodec,
    BytesCodec,
    DatetimeCodec,
    EnumCodec,
    ListCodec,
    ModelCodec,
    StrCodec,
    UUIDCodec,
    VarIntCodec,
)
from .missing import MISSING
from .models import FieldInfo, ResolvedType

ResolveCallback: TypeAlias = Callable[[Any, FieldInfo], ResolvedType]


class CodecFactory(Protocol):
    """Codec factory returned by rules configured via `configure_codecs()`.

    When selecting a codec for a scalar field, it is called with two arguments:
    the annotation and `FieldInfo`. It returns a ready-to-use codec instance.
    The third protocol argument is optional and is not passed in this path.
    """

    def __call__(
        self, annotation: Any, field_info: FieldInfo, resolve: ResolveCallback | None = None, /
    ) -> ICodec[Any]: ...


def str_codec_factory(_: Any, field_info: FieldInfo, __: ResolveCallback | None = None) -> StrCodec:

    if field_info.prefix_length is not None:
        return StrCodec(prefix_length=field_info.prefix_length, encoding=field_info.encoding)
    return StrCodec(encoding=field_info.encoding)


def bytes_codec_factory(
    _: Any, field_info: FieldInfo, __: ResolveCallback | None = None
) -> BytesCodec:
    if field_info.prefix_length is not None:
        return BytesCodec(prefix_length=field_info.prefix_length)
    return BytesCodec()


def datetime_codec_factory(
    _: Any, field_info: FieldInfo, __: ResolveCallback | None = None
) -> DatetimeCodec:
    if field_info.prefix_length is not None:
        return DatetimeCodec(prefix_length=field_info.prefix_length, encoding=field_info.encoding)
    return DatetimeCodec(encoding=field_info.encoding)


def model_codec_factory(
    annotation: Any, _: FieldInfo, __: ResolveCallback | None = None
) -> ModelCodec:
    return ModelCodec(annotation)


def int_codec_factory(_: Any, __: FieldInfo, ___: ResolveCallback | None = None) -> VarIntCodec:
    return VarIntCodec()


def enum_codec_factory(
    annotation: Any, field_info: FieldInfo, __: ResolveCallback | None = None
) -> EnumCodec:
    if not issubclass(annotation, Enum):
        raise SchemaError(f"Unknown enum type: {annotation}")

    if issubclass(annotation, str):
        return EnumCodec(annotation, str_codec_factory(annotation, field_info, __))
    if issubclass(annotation, int):
        return EnumCodec(annotation, int_codec_factory(annotation, field_info, __))
    raise SchemaError(f"Unknown enum type: {annotation}")


def bool_codec_factory(_: Any, __: FieldInfo, ___: ResolveCallback | None = None) -> BoolCodec:
    return BoolCodec()


def uuid_codec_factory(_: Any, __: FieldInfo, ___: ResolveCallback | None = None) -> UUIDCodec:
    return UUIDCodec()


def list_codec_factory(
    annotation: Any, field_info: FieldInfo, callback: ResolveCallback
) -> ListCodec:
    metadata = list(get_args(annotation))

    if len(metadata) != 1:
        raise SchemaError(f"Unsupported list type: {annotation}")

    resolved_type = callback(metadata[0], FieldInfo(None, None, MISSING, MISSING, None))

    if resolved_type.optional:
        raise SchemaError(f"Unsupported list type: {annotation}")

    if field_info.prefix_length is not None:
        return ListCodec(resolved_type.codec, field_info.prefix_length)
    return ListCodec(resolved_type.codec)
