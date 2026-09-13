# Copyright (c) 2026 ink-developer

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from bytespec.codecs import ICodec
from bytespec.enums import ByteOrder

if TYPE_CHECKING:
    from bytespec.core import ProtoModel
    from bytespec.enums import ByteOrder


class ModelCodec(ICodec["ProtoModel"]):
    """A nested model with its own framing, excluding Constructor, and its own byte order.

    Args:
        model_type: The concrete class to read via decode_from(). Subclasses are not selected
            automatically by constructor.
    """

    def __init__(self, model_type: type[ProtoModel]) -> None:
        self.model_type = model_type

    @override
    def encode(self, value: ProtoModel, _: ByteOrder) -> bytes:
        """Write value using its own settings, skipping Constructor elements."""
        return value.encode(include_constructor=False)

    @override
    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int) -> tuple[ProtoModel, int]:
        """Read model_type and return the instance with its absolute end offset.

        The outer byte_order is ignored: model_type settings are used. Errors propagate from
        model_type.decode_from().
        """
        return self.model_type.decode_from(buffer, offset, expect_constructor=False)
