from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .enums import ByteOrder

if TYPE_CHECKING:
    from .core import FieldMetadata, ProtoModel
    from .headers import HeaderElement


@dataclass(frozen=True, slots=True)
class ModelSchema:
    model: type[ProtoModel]
    fields: tuple[FieldMetadata, ...]
    header: tuple[HeaderElement, ...]
    byte_order: ByteOrder
    constructor: int | None


@dataclass(slots=True)
class HeaderEncodeContext:
    schema: ModelSchema
    include_constructor: bool
    payload_length: int
    flags: int


@dataclass(slots=True)
class HeaderDecodeContext:
    schema: ModelSchema
    expect_constructor: bool
    payload_length: int | None = None
    flags: int = 0
