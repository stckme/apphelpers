from dataclasses import dataclass, asdict


def phony(f):
    return f


@dataclass
class User:
    sid: str = None
    id: int = None
    name: str = None
    groups: tuple = ()
    email: str = None
    mobile: str = None
    site_groups: dict = None

    def to_dict(self):
        return asdict(self)

    def __bool__(self):
        return bool(self.id)
