from dataclasses import dataclass
from typing import ClassVar

from fastapi import HTTPException, status


@dataclass
class BaseError(HTTPException):
    # Whether to report this error to honeybadger
    report: ClassVar[bool] = True

    detail: str = "Something went wrong"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


@dataclass
class HTTP400BadRequest(BaseError):
    detail: str = "Bad Request"
    status_code = status.HTTP_400_BAD_REQUEST


@dataclass
class HTTP401Unauthorized(BaseError):
    detail: str = "Unauthorized"
    status_code = status.HTTP_401_UNAUTHORIZED


@dataclass
class HTTP403Forbidden(BaseError):
    detail: str = "Forbidden"
    status_code = status.HTTP_403_FORBIDDEN


@dataclass
class HTTP404NotFound(BaseError):
    detail: str = "Not Found"
    status_code = status.HTTP_404_NOT_FOUND


@dataclass
class HTTP409Conflict(BaseError):
    detail: str = "Conflict"
    status_code = status.HTTP_409_CONFLICT


@dataclass
class InvalidSessionError(HTTP401Unauthorized):
    detail: str = "Invalid Session"
