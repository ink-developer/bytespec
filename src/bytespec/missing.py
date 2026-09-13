# Copyright (c) 2026 ink-developer

from typing import Final, TypeAlias

from typing_extensions import override


class _MissingType:
    __slots__ = ()

    @override
    def __repr__(self) -> str:
        return "MISSING"


MISSING: Final = _MissingType()
MissingType: TypeAlias = _MissingType
