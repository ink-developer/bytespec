# Copyright (c) 2026 ink-developer

from typing import Annotated, Any

from bytespec.codecs.base import ICodec
from bytespec.codecs.varint import VarUIntCodec
from bytespec.types import VarUInt

from .int import UInt8Codec, UInt16Codec, UInt32Codec, UInt64Codec

UINT_CODEC_MAPPING: dict[int | Annotated[Any, Any], ICodec[Any]] = {
    1: UInt8Codec(),
    2: UInt16Codec(),
    4: UInt32Codec(),
    8: UInt64Codec(),
    VarUInt: VarUIntCodec(),
}
