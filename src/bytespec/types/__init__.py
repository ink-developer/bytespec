# Copyright (c) 2026 ink-developer

from typing import Annotated, TypeAlias

from .spec import CodecSpec as CodecSpec
from .spec import FloatSpec, IntegerSpec, VarIntSpec
from .spec import Spec as Spec

UInt8 = Annotated[int, IntegerSpec(8, signed=False)]
UInt16 = Annotated[int, IntegerSpec(16, signed=False)]
UInt32 = Annotated[int, IntegerSpec(32, signed=False)]
UInt64 = Annotated[int, IntegerSpec(64, signed=False)]

Int8 = Annotated[int, IntegerSpec(8, signed=True)]
Int16 = Annotated[int, IntegerSpec(16, signed=True)]
Int32 = Annotated[int, IntegerSpec(32, signed=True)]
Int64 = Annotated[int, IntegerSpec(64, signed=True)]

Float32 = Annotated[float, FloatSpec(32)]
Float64 = Annotated[float, FloatSpec(64)]

VarUInt = Annotated[int, VarIntSpec(signed=False)]
VarInt = Annotated[int, VarIntSpec(signed=True)]

UIntUnion: TypeAlias = UInt16 | UInt32 | UInt64 | UInt8
