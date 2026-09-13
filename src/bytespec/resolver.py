# Copyright (c) 2026 ink-developer

import codecs
from enum import Enum
from types import NoneType, UnionType
from typing import Annotated, Any, Union, get_args, get_origin

from bytespec.base import ProtoModelBase
from bytespec.codecs import (
    Float32Codec,
    Float64Codec,
    ICodec,
    UInt8Codec,
    VarIntCodec,
    VarUIntCodec,
)
from bytespec.codecs.int import (
    Int8Codec,
    Int16Codec,
    Int32Codec,
    Int64Codec,
    UInt16Codec,
    UInt32Codec,
    UInt64Codec,
)
from bytespec.errors import SchemaError
from bytespec.models import FieldInfo, ResolvedType
from bytespec.resolvers import (
    CodecFactory,
    ResolveCallback,
    enum_codec_factory,
    list_codec_factory,
    model_codec_factory,
)
from bytespec.types import CodecSpec, FloatSpec, IntegerSpec, Spec
from bytespec.types.spec import VarIntSpec

INTEGER_CODECS: dict[tuple[int, bool], type[ICodec[Any]]] = {
    (8, False): UInt8Codec,
    (16, False): UInt16Codec,
    (32, False): UInt32Codec,
    (64, False): UInt64Codec,
    (8, True): Int8Codec,
    (16, True): Int16Codec,
    (32, True): Int32Codec,
    (64, True): Int64Codec,
}
FLOAT_CODECS: dict[int, type[ICodec[Any]]] = {
    32: Float32Codec,
    64: Float64Codec,
}
VARINT_CODECS: dict[bool, type[ICodec[Any]]] = {
    True: VarIntCodec,
    False: VarUIntCodec,
}


def resolve_integer(_: Any, spec: IntegerSpec, __: FieldInfo, ___: ResolveCallback) -> ICodec[Any]:
    codec = INTEGER_CODECS.get((spec.bits, spec.signed))

    if not codec:
        raise SchemaError(f"Unsupported numeric spec: {spec!r}")

    return codec()


def resolve_float(_: Any, spec: FloatSpec, __: FieldInfo, ___: ResolveCallback) -> ICodec[Any]:
    codec = FLOAT_CODECS.get(spec.bits)

    if not codec:
        raise SchemaError(f"Unsupported numeric spec: {spec!r}")

    return codec()


def resolve_varint(_: Any, spec: VarIntSpec, __: FieldInfo, ___: ResolveCallback) -> ICodec[Any]:
    codec = VARINT_CODECS.get(spec.signed)

    if not codec:
        raise SchemaError(f"Unsupported numeric spec: {spec!r}")

    return codec()


class CodecResolver:
    def __init__(self, scalar_codecs: dict[type, CodecFactory]) -> None:
        self.scalar_codecs = scalar_codecs

    def _is_type_of(self, annotation: Any, subclass: type) -> bool:
        return isinstance(annotation, type) and issubclass(annotation, subclass)

    def _normalize_union(self, annotation: Any | UnionType) -> tuple[Any, bool]:
        is_optional = False
        metadata = list(get_args(annotation))

        if NoneType in metadata:
            is_optional = True
            metadata.pop(metadata.index(NoneType))

        if len(metadata) > 1:
            raise SchemaError(f"Unsupported union type: {annotation}")

        return metadata[0], is_optional

    def _check_encoding(self, encoding: str) -> None:
        try:
            codecs.lookup(encoding)
        except LookupError as exc:
            raise SchemaError(f"Invalid encoding: {encoding!r}") from exc

    def _resolve_spec(
        self,
        base_type: Any,
        spec: Spec,
        field_info: FieldInfo,
        resolve: ResolveCallback,
    ) -> ICodec[Any]:
        if isinstance(spec, IntegerSpec):
            return resolve_integer(base_type, spec, field_info, resolve)

        if isinstance(spec, FloatSpec):
            return resolve_float(base_type, spec, field_info, resolve)

        if isinstance(spec, VarIntSpec):
            return resolve_varint(base_type, spec, field_info, resolve)

        raise SchemaError(f"Unsupported spec: {type(spec).__name__}")

    def resolve(
        self, annotation: Any, field_info: FieldInfo, is_optional: bool = False
    ) -> ResolvedType:
        self._check_encoding(field_info.encoding)

        origin = get_origin(annotation)

        if origin in (UnionType, Union):
            annotation, is_optional = self._normalize_union(annotation)

        if field_info.codec is not None:
            return ResolvedType(
                field_info.codec,
                is_optional,
                annotation,
            )

        scalar_codec = self.scalar_codecs.get(annotation)

        if scalar_codec:
            return ResolvedType(scalar_codec(annotation, field_info), is_optional, annotation)

        if get_origin(annotation) is Annotated:
            base_type, *metadata = get_args(annotation)

            specs = [meta for meta in metadata if isinstance(meta, Spec)]

            if len(specs) > 1:
                raise SchemaError("Only one Spec is allowed")

            if not specs:
                return self.resolve(base_type, field_info, is_optional)

            spec = specs[0]

            if isinstance(spec, CodecSpec):
                if spec.prefix_length is not None:
                    field_info.prefix_length = spec.prefix_length

                if spec.encoding:
                    self._check_encoding(spec.encoding)
                    field_info.encoding = spec.encoding

                if spec.codec is not None:
                    field_info.codec = spec.codec

                return self.resolve(base_type, field_info, is_optional)

            return ResolvedType(
                self._resolve_spec(base_type, spec, field_info, self.resolve),
                is_optional,
                annotation,
            )

        if self._is_type_of(annotation, ProtoModelBase):
            return ResolvedType(
                model_codec_factory(annotation, field_info), is_optional, annotation
            )

        if self._is_type_of(annotation, Enum):
            return ResolvedType(
                enum_codec_factory(annotation, field_info), is_optional, annotation
            )

        if get_origin(annotation) is list:
            return ResolvedType(
                list_codec_factory(annotation, field_info, self.resolve), is_optional, annotation
            )

        raise SchemaError(f"Unknown type: {annotation}")
