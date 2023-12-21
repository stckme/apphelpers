from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)
from typing import (
    Dict,
    List,
    Optional,
)


def phony(f):
    return f


@dataclass
class User:
    sid: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    groups: List[str] = field(default_factory=list)
    email: Optional[str] = None
    mobile: Optional[str] = None
    site_groups: Dict[int, int] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    def __bool__(self):
        return self.id is not None
