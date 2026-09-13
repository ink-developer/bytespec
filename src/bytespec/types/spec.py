# Copyright (c) 2026 ink-developer

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from bytespec.codecs import ICodec

if TYPE_CHECKING:
    from bytespec.models import PrefixLength


@dataclass(frozen=True)
class IntegerSpec:
    """Select a fixed-width integer in ``Annotated[int, ...]``.

    Args:
        bits: The number of bits: 8, 16, 32, or 64.
        signed: Allow negative values (signed representation).
    """

    bits: Literal[8, 16, 32, 64]
    signed: bool


@dataclass(frozen=True)
class FloatSpec:
    """Select an IEEE 754 number in ``Annotated[float, ...]``.

    Args:
        bits: The number of bits: 32 or 64. Float32 rounds a Python float to its representation.
    """

    bits: Literal[32, 64]


@dataclass(frozen=True)
class VarIntSpec:
    """Select a varint in ``Annotated[int, ...]``.

    Args:
        signed: If True, use ZigZag and the Int64 range; if False, use an unsigned varint and the
            UInt64 range.
    """

    signed: bool


@dataclass(frozen=True)
class StructSpec:
    struct_format: str


@dataclass(frozen=True)
class CodecSpec:
    """Define reusable field settings using ``Annotated``.

    Args:
        prefix_length: Prefix size: 1, 2, 4, or 8 bytes, or ``VarUInt``. ``None`` leaves the field
            setting unchanged; ``VarInt`` is not supported.
        encoding: The text encoding. A nonempty value replaces the field encoding.
        codec: A ready-to-use codec instance instead of automatic selection.

    Note:
        One supported specification is allowed per Annotated. An explicit ``field(codec=...)`` takes
        precedence over CodecSpec.
    """

    prefix_length: PrefixLength | None = None
    encoding: str | None = None
    codec: ICodec[Any] | None = None


Spec: TypeAlias = IntegerSpec | FloatSpec | VarIntSpec | CodecSpec
