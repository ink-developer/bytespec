# Copyright (c) 2026 ink-developer

from typing import Any, Generic, Protocol, TypeVar

from typing_extensions import runtime_checkable

from bytespec.enums import ByteOrder

T = TypeVar("T")


@runtime_checkable
class ICodec(Protocol, Generic[T]):
    """Interface for writing and reading a single value of type T.

    An instance can be passed to ``field(codec=...)``. Inheriting from ICodec is optional: encode
    and decode methods that follow this contract are sufficient. A codec can be reused; the read
    position is passed through offset.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()

    def encode(self, value: T, byte_order: ByteOrder, /) -> bytes:
        """Write a single value in the selected representation.

        Args:
            value: The value to write.
            byte_order: The byte order of fixed-width numbers and prefixes.

        Returns:
            The binary representation of the value.

        Raises:
            EncodeError: The value cannot be represented. A custom codec must raise this error
                itself for data errors.
        """
        ...

    def decode(self, buffer: bytes, byte_order: ByteOrder, offset: int, /) -> tuple[T, int]:
        """Read a single value starting at offset.

        Args:
            buffer: The buffer containing the encoded value.
            byte_order: The byte order of fixed-width numbers and prefixes.
            offset: The nonnegative absolute position where the value starts.

        Returns:
            The value and the absolute position after it in the same buffer. The remaining bytes do
            not have to be consumed.

        Raises:
            DecodeError: There are not enough bytes, or the value is invalid. The implementation
                must check bounds and contents itself.

        Note:
            A list item codec must advance offset by a positive number of bytes while staying within
            the supplied buffer.
        """
        ...
