# Copyright (c) 2026 ink-developer

from types import NoneType, UnionType
from typing import Annotated, Any, ClassVar, Final, Union, get_args, get_origin

from bytespec.enums import ByteOrder
from bytespec.headers import Constructor, Flags, HeaderElement, PayloadLength
from bytespec.resolvers import CodecFactory
from bytespec.schema import ModelSchema

DEFAULT_HEADER: Final[tuple[HeaderElement, ...]] = (Constructor(2), Flags(8), PayloadLength(4))


class ProtoModelBase:
    __constructor__: int = 0x1
    __byte_order__: ByteOrder = ByteOrder.BIG
    __header__: ClassVar[tuple[HeaderElement, ...]] = DEFAULT_HEADER
    __schema__: ModelSchema

    @classmethod
    def _is_valid_value(cls, value: Any, annotation: Any) -> bool:
        origin = get_origin(annotation)

        if origin is Annotated:
            base_type, *_ = get_args(annotation)
            return cls._is_valid_value(value, base_type)

        if origin in (Union, UnionType):
            return any(
                (arg is NoneType and value is None)
                or (arg is not NoneType and cls._is_valid_value(value, arg))
                for arg in get_args(annotation)
            )

        if origin is list:
            return isinstance(value, list)

        return isinstance(value, annotation)

    @classmethod
    def configure_codecs(cls) -> dict[type, CodecFactory]:
        """Define additional codec selection rules for field types.

        Override this classmethod in the model. Rules apply at class declaration, extending
        inherited rules and replacing matching keys.

        Returns:
            A mapping from Python types to codec factories. A factory receives the annotation and
            ``FieldInfo`` and returns a ready-to-use codec instance. There are no additional rules
            by default.
        """
        return {}
