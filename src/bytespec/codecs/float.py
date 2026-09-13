# Copyright (c) 2026 ink-developer

from .int import IntegerCodec


class Float32Codec(IntegerCodec[float]):
    """IEEE 754 binary32: four bytes, rounding the Python float."""

    def __init__(self, struct_format: str = "f", length: int = 4) -> None:
        super().__init__(struct_format, length)


class Float64Codec(Float32Codec):
    """IEEE 754 binary64: eight bytes in the model's byte order."""

    def __init__(self, struct_format: str = "d", length: int = 8) -> None:
        super().__init__(struct_format, length)
