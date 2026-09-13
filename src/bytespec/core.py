# Copyright (c) 2026 ink-developer

from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    ClassVar,
    get_type_hints,
)
from uuid import UUID

from typing_extensions import Self, dataclass_transform, override

from bytespec.base import DEFAULT_HEADER, ProtoModelBase
from bytespec.codecs import ICodec
from bytespec.codecs._utils import check_available
from bytespec.headers import Flags
from bytespec.missing import MISSING, MissingType
from bytespec.models import DefaultFactory, FieldInfo, PrefixLength
from bytespec.resolver import CodecResolver
from bytespec.resolvers import (
    CodecFactory,
    bool_codec_factory,
    bytes_codec_factory,
    datetime_codec_factory,
    int_codec_factory,
    str_codec_factory,
    uuid_codec_factory,
)
from bytespec.schema import HeaderDecodeContext, HeaderEncodeContext, ModelSchema

from .errors import DecodeError, EncodeError, SchemaError


@dataclass
class FieldMetadata:
    name: str
    index: int
    flag: int | None
    default: Any
    default_factory: DefaultFactory
    annotation: Any
    codec: ICodec[Any]


def field(
    index: int | None = None,
    *,
    flag: int | None = None,
    default: Any = MISSING,
    default_factory: DefaultFactory = MISSING,
    prefix_length: PrefixLength | None = None,
    encoding: str = "utf-8",
    codec: ICodec[Any] | None = None,
) -> Any:
    """Configure a serializable model field.

    Args:
        index: The field position, starting at zero. If omitted, the smallest available index is
            selected in field declaration order.
        flag: The presence bit number (0–63). Required for ``T | None``; must be unique and fit
            within the model's flags size.
        default: The value used when the constructor argument is omitted. Explicit ``None`` differs
            from having no default and is only valid for optional fields.
        default_factory: A function with no arguments that creates a value when the field is
            omitted. Cannot be specified together with ``default``.
        prefix_length: The length prefix size: 1, 2, 4, or 8 bytes, or ``VarUInt``. ``None`` keeps
            the codec's default setting. For a list, configures the list itself, not its items.
        encoding: The encoding of text values. Defaults to UTF-8.
        codec: A ready-to-use codec instance that replaces automatic selection. Other field settings
            do not reconfigure this instance.

    Returns:
        A field description for use in the body of a model class.

    Note:
        Setting compatibility is checked at model declaration. Unsupported or conflicting settings
        raise ``SchemaError``.
    """
    return FieldInfo(
        index=index,
        flag=flag,
        default=default,
        default_factory=default_factory,
        prefix_length=prefix_length,
        encoding=encoding,
        codec=codec,
    )


@dataclass_transform(field_specifiers=(field,))
class ProtoModel(ProtoModelBase):
    """The base model class for binary serialization.

    Declare fields using annotations and create an instance with keyword arguments. ``encode()``
    writes a message; ``decode()`` reconstructs an instance of the same class. Use ``field()`` to
    configure individual fields.

    Args:
        **kwargs: Field values. Omitted fields receive a default, the result of a factory, or
            ``None`` for optional fields; all other fields are required.

    Note:
        Annotations define the binary format, but explicitly supplied values are not fully
        type-checked by the constructor. Fields are mutable. The schema is validated when a subclass
        is declared. If a subclass declares its own fields, the parent's serializable fields are not
        merged with them.
    """

    _scalar_codecs: ClassVar[dict[type, CodecFactory]] = {
        int: int_codec_factory,
        str: str_codec_factory,
        bool: bool_codec_factory,
        bytes: bytes_codec_factory,
        datetime: datetime_codec_factory,
        UUID: uuid_codec_factory,
    }
    _resolver = CodecResolver(_scalar_codecs)

    def __init__(self, **kwargs: Any) -> None:
        """Create an instance from named field values.

        Args:
            **kwargs: Values of declared fields; omitted fields use the default, factory, or
                ``None`` for optional fields.

        Raises:
            TypeError: An unknown field, a missing required field, or an invalid type for a default
                value or factory result.

        Note:
            After assigning the fields, ``__validate__`` is called if defined directly on the
            concrete class. Its exceptions are not wrapped.
        """
        field_names = {field.name for field in self.__schema__.fields}
        unknown = kwargs.keys() - field_names

        if unknown:
            raise TypeError(f"Unknown fields: {', '.join(unknown)}")

        for field in self.__schema__.fields:
            value = kwargs.get(field.name, MISSING)

            if value is MISSING:
                if field.default is not MISSING and field.default_factory is not MISSING:
                    raise SchemaError(
                        f"{field.name}: default and default_factory cannot be specified together"
                    )

                if field.default is not MISSING:
                    value = field.default

                elif not isinstance(field.default_factory, MissingType):
                    value = field.default_factory()
                elif field.flag is not None:
                    value = None
                else:
                    raise TypeError(f"Missing required field: {field.name}")

                if not self._is_valid_value(value, field.annotation):
                    raise TypeError(
                        f"{field.name}: invalid default value {value!r}; expected {field.annotation}, got {type(value).__name__}"
                    )

            setattr(self, field.name, value)

        validator = type(self).__dict__.get("__validate__")

        if validator is not None:
            validator(self)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        model_codecs = cls._scalar_codecs.copy()
        model_codecs.update(cls.configure_codecs())
        cls._scalar_codecs = model_codecs
        cls._resolver.scalar_codecs = cls._scalar_codecs

        if "__header__" not in cls.__dict__:
            proto_bases = [base for base in cls.__bases__ if issubclass(base, ProtoModelBase)]
            custom_headers = [
                base.__header__ for base in proto_bases if base.__header__ is not DEFAULT_HEADER
            ]

            if custom_headers:
                first_header = custom_headers[0]

                if not all(header is first_header for header in custom_headers):
                    raise SchemaError(
                        f"{cls.__name__}: conflicting inherited headers; define __header__ explicitly"
                    )

                cls.__header__ = first_header

        fields: list[FieldMetadata] = []

        indexes: set[int] = set()
        flags: set[int] = set()

        try:
            raw_annotations = cls.__annotations__
            resolved_annotations = get_type_hints(cls, include_extras=True)
        except (NameError, TypeError) as exc:
            raise SchemaError(f"{cls.__name__}: cannot resolve annotations: {exc}") from exc

        for name, value in cls.__dict__.items():
            if isinstance(value, FieldInfo) and name not in raw_annotations:
                raise SchemaError(f"{cls.__name__}.{name}: field requires a type annotation")

        for name in raw_annotations:
            annotation = resolved_annotations[name]
            raw_value = cls.__dict__.get(name, MISSING)

            if raw_value is MISSING:
                value = FieldInfo(None, None, MISSING, MISSING, None)
            elif isinstance(raw_value, FieldInfo):
                value = raw_value
            else:
                continue

            if value.default is not MISSING and value.default_factory is not MISSING:
                raise SchemaError(
                    f"{cls.__name__}.{name}: default and default_factory cannot be specified together"
                )

            try:
                resolved_type = cls._resolver.resolve(annotation, value)
            except SchemaError as exc:
                exc.args = (f"{cls.__name__}.{name}: {exc}",)
                raise

            if value.default is not MISSING:
                if value.default is None:
                    if not resolved_type.optional:
                        raise SchemaError(
                            f"{cls.__name__}.{name}: None default requires an optional field"
                        )
                elif not cls._is_valid_value(value.default, resolved_type.annotation):
                    raise SchemaError(
                        f"Invalid default value: {value.default!r}. "
                        + f"Expected {resolved_type.annotation}, "
                        + f"got {type(value.default).__name__}"
                    )

            if value.flag is not None and not resolved_type.optional:
                raise SchemaError(f"{cls.__name__}.{name}: flag requires an optional field")

            if resolved_type.optional:
                if value.flag is None:
                    raise SchemaError(
                        f"{annotation} is a UnionType with NoneType but no flag index presented"
                    )
                if not isinstance(value.flag, int) or not 0 <= value.flag < 64:
                    raise SchemaError(
                        f"{cls.__name__}.{name}: flag {value.flag!r} must be in range 0..63"
                    )

                if value.flag in flags:
                    raise SchemaError(f"{cls.__name__}.{name}: duplicate flag {value.flag}")

                flags.add(value.flag)

            if value.index is not None:
                index = value.index
                if not isinstance(index, int) or index < 0:
                    raise SchemaError(f"{cls.__name__}.{name}: invalid field index {index!r}")
            else:
                index = 0
                while index in indexes:
                    index += 1

            codec = resolved_type.codec if not value.codec else value.codec

            if not isinstance(codec, ICodec):
                raise SchemaError(f"Invalid codec type: {type(codec)}")

            fields.append(
                FieldMetadata(
                    name=name,
                    index=index,
                    flag=value.flag,
                    annotation=annotation,
                    codec=codec,
                    default=value.default,
                    default_factory=value.default_factory,
                )
            )

            if isinstance(raw_value, FieldInfo):
                delattr(cls, name)

            indexes.add(index)

        fields.sort(key=lambda x: x.index)
        own_fields = fields

        parent_fields = cls.__schema__.fields if getattr(cls, "__schema__", None) else ()

        effective_fields = tuple(own_fields or parent_fields)

        has_flags = any(isinstance(element, Flags) for element in cls.__header__)

        if any(field.flag is not None for field in effective_fields) and not has_flags:
            raise SchemaError("Found optional fields in model but no Flags presented in header")

        if fields and (
            min(indexes) != 0 or max(indexes) != len(fields) - 1 or max(indexes) != len(indexes) - 1
        ):
            raise SchemaError(
                f"{cls.__name__}: field indexes must be unique and contiguous from 0, got {[field.index for field in fields]}"
            )

        cls.__schema__ = ModelSchema(
            model=cls,
            fields=effective_fields,
            header=cls.__header__,
            byte_order=cls.__byte_order__,
            constructor=cls.__constructor__,
        )

        for header in cls.__schema__.header:
            header.validate(cls.__schema__)

    def encode(self, include_constructor: bool = True) -> bytes:
        """Write the current model state as a single binary message.

        Args:
            include_constructor: Write Constructor elements from __header__. False omits them
                entirely, retaining the other elements.

        Returns:
            The __header__ elements in the specified order, followed by the fields. Optional fields
            whose value is ``None`` are not written.

        Raises:
            EncodeError: A required value is missing, or a field value cannot be written in the
                selected representation.

        Note:
            Implementation errors in a custom codec are not wrapped automatically. __validate__ is
            not called again.
        """
        flags: int = 0  # u64
        payload: bytes = b""

        for field in self.__schema__.fields:
            value = getattr(self, field.name, MISSING)

            if value is MISSING or (value is None and field.flag is None):
                raise EncodeError(f"{type(self).__name__}.{field.name}: missing required value")

            if value is None:
                continue

            if field.flag is not None:
                flags |= 1 << field.flag

            try:
                payload += field.codec.encode(value, self.__byte_order__)
            except EncodeError as exc:
                exc.args = (f"{type(self).__name__}.{field.name}: {exc}",)
                raise

        ctx = HeaderEncodeContext(self.__schema__, include_constructor, len(payload), flags)

        header = b"".join(element.encode(ctx) for element in self.__header__)

        return header + payload

    @classmethod
    def decode_from(
        cls,
        buffer: bytes,
        offset: int,
        expect_constructor: bool = True,
    ) -> tuple[Self, int]:
        """Read a single message from the specified position in a buffer.

        Args:
            buffer: A buffer containing the complete message.
            offset: The nonnegative absolute position where the message starts.
            expect_constructor: Read and validate Constructor elements. False omits them entirely;
                the corresponding bytes must not be present in the input.

        Returns:
            A pair containing the new instance and the absolute position after the message. The
            position can be passed to the next call to read the following message.

        Raises:
            DecodeError: Incomplete or invalid data, an incorrect constructor, or a field extending
                beyond the declared payload bounds.
            ValueError: Negative offset.

        Note:
            Trailing data within the declared payload and unknown flag bits are skipped without
            being preserved. Bytes after the message are left to the caller. Network fragments are
            not accumulated between calls. Without PayloadLength, the end is determined by the known
            fields, with no separate body boundary. Creating the instance runs its own __validate__;
            validator exceptions propagate without wrapping.
        """
        ctx = HeaderDecodeContext(cls.__schema__, expect_constructor)

        for element in cls.__header__:
            offset = element.decode(buffer, offset, ctx)

        if ctx.payload_length is not None:
            payload_start = offset
            payload_end = payload_start + ctx.payload_length

            check_available(buffer, payload_start, ctx.payload_length, codec=cls.__name__)
            payload_buffer = buffer[:payload_end]
        else:
            payload_buffer = buffer
            payload_end = None

        args = {}

        for field in cls.__schema__.fields:  # it already sorted i think
            if field.flag is not None and not (ctx.flags & (1 << field.flag)):
                args[field.name] = None
                continue

            try:
                value, offset = field.codec.decode(payload_buffer, cls.__byte_order__, offset)
            except DecodeError as exc:
                exc.args = (f"{cls.__name__}.{field.name}: {exc}",)
                raise
            args[field.name] = value

            if payload_end is not None and offset > payload_end:
                raise DecodeError(
                    f"{cls.__name__}.{field.name} at offset {offset}: exceeds payload boundary {payload_end}"
                )

        if payload_end is not None and offset > payload_end:
            raise DecodeError(
                f"{cls.__name__} at offset {offset}: decoded past payload boundary {payload_end}"
            )

        if payload_end is not None:
            offset = payload_end

        return cls(**args), offset

    @classmethod
    def decode(cls, buffer: bytes) -> Self:
        """Reconstruct a model from a buffer containing exactly one message.

        Args:
            buffer: A complete binary message matching the model class.

        Returns:
            A new instance of the class with the field values read from the buffer.

        Raises:
            DecodeError: Incomplete/invalid data, an incorrect constructor, or extra bytes after the
                end of the message.

        Note:
            For multiple messages in a single buffer, use ``decode_from``. Unknown trailing data
            within the declared payload is skipped.
        """
        model, offset = cls.decode_from(buffer, 0)

        if offset != len(buffer):
            raise DecodeError(
                f"{cls.__name__} at offset {offset}: trailing data, {len(buffer) - offset} bytes"
            )

        return model

    @override
    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented

        return all(
            getattr(self, field.name) == getattr(other, field.name)
            for field in self.__schema__.fields
        )

    @override
    def __repr__(self) -> str:
        fields = ", ".join(
            f"{field.name}={getattr(self, field.name)!r}" for field in self.__schema__.fields
        )
        return f"{type(self).__name__}({fields})"

    def __validate__(self) -> None:
        """Validate relationships between field values that have already been assigned.

        Override this method in a concrete model and raise an exception if an invariant is violated.
        The return value is ignored. The method is called automatically at the end of __init__,
        including during decode, only if it is defined on the concrete class itself. To run parent
        validation, call super().__validate__() from the child method.

        Attribute assignments and encode do not call the method again. User exceptions propagate
        without wrapping.
        """
