# Copyright (c) 2026 ink-developer


class BytespecError(Exception):
    """Common base class for schema, encoding, and decoding errors."""


class SchemaError(BytespecError):
    """Unsupported or conflicting model or codec types/settings.

    Usually raised when declaring a model or creating a codec. Some configuration errors, such as a
    non-text string encoding, surface during writing or reading.
    """


class EncodeError(BytespecError):
    """The value cannot be written in the selected binary representation.

    For example, a number outside its range, a length prefix overflow, text that cannot be
    represented in the encoding, or a missing required value.
    """


class DecodeError(BytespecError):
    """The buffer is incomplete or does not match the expected binary format.

    For example, an incorrect constructor, missing bytes, an invalid value, or data after the
    message when calling ``ProtoModel.decode()``.
    """
