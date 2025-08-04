from dataclasses import dataclass
from typing import ClassVar

from fastapi import HTTPException, status


@dataclass
class BaseError(HTTPException):
    # Whether to report this error to honeybadger
    report: ClassVar[bool] = True
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: ClassVar[str] = "Something went wrong"


@dataclass
class HTTP400BadRequest(BaseError):
    status_code: ClassVar[int] = status.HTTP_400_BAD_REQUEST
    detail: str = "Bad Request"


@dataclass
class HTTP401Unauthorized(BaseError):
    status_code: ClassVar[int] = status.HTTP_401_UNAUTHORIZED
    detail: str = "Unauthorized"


@dataclass
class HTTP403Forbidden(BaseError):
    status_code: ClassVar[int] = status.HTTP_403_FORBIDDEN
    detail: str = "Forbidden"


@dataclass
class HTTP404NotFound(BaseError):
    status_code: ClassVar[int] = status.HTTP_404_NOT_FOUND
    detail: str = "Not Found"


@dataclass
class HTTP409Conflict(BaseError):
    status_code: ClassVar[int] = status.HTTP_409_CONFLICT
    detail: str = "Conflict"


@dataclass
class InvalidSessionError(HTTP401Unauthorized):
    detail: str = "Invalid Session"
