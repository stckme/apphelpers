from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class BaseError(Exception):

    # Whether to report this error to honeybadger
    report: bool = True
    msg: str = ""
    code: Optional[int] = None
    data: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class NotFoundError(BaseError):
    code: int = 404


@dataclass
class SecurityViolation(BaseError):
    pass


@dataclass
class AccessDenied(BaseError):
    msg: str = "Access denied"


@dataclass
class ValidationError(BaseError):
    code: int = 400


@dataclass
class InvalidSessionError(BaseError):
    code: int = 401
    msg: str = "Invalid session"


@dataclass
class ConflictError(BaseError):
    code: int = 409
    msg: str = "Duplicate resource"
