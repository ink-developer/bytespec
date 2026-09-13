# Copyright (c) 2026 ink-developer

from enum import Enum


class ByteOrder(str, Enum):
    """The byte order of the model's fixed-width numbers and prefixes.

    ``BIG`` means big-endian (``>``), and ``LITTLE`` means little-endian (``<``). This setting does
    not affect varints, bytes contents, or the UUID representation.
    """

    BIG = ">"
    LITTLE = "<"
