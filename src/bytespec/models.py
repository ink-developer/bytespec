# Copyright (c) 2026 ink-developer

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from bytespec.codecs import ICodec
from bytespec.missing import MissingType
from bytespec.types import VarUInt

DefaultFactory: TypeAlias = Callable[[], Any] | MissingType

UIntEncoding = Literal[1, 2, 4, 8] | VarUInt
PrefixLength = UIntEncoding


@dataclass
class FieldInfo:
    """Field settings passed to a user-defined codec factory.

    In models, create them via `field()`. The factory may read
    `prefix_length`, `encoding`, and other settings to construct a codec.

    Args:
        index: Explicit field position, or None for automatic selection.
        flag: Presence bit index for an optional field, or None.
        default: Default value or the MISSING sentinel.
        default_factory: Zero-argument factory or MISSING.
        prefix_length: Length prefix size, or None to use the default.
        encoding: Text encoding, UTF-8 by default.
        codec: Explicitly assigned codec instance, or None.
    """

    index: int | None
    flag: int | None
    default: Any
    default_factory: DefaultFactory
    prefix_length: PrefixLength | None
    encoding: str = "utf-8"
    codec: ICodec[Any] | None = None


@dataclass
class ResolvedType:
    codec: ICodec[Any]
    optional: bool
    annotation: Any
