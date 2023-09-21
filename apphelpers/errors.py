from falcon import HTTPError, status_codes


class BaseError(HTTPError):

    # Whether to report this error to honeybadger
    report = True

    status = status_codes.HTTP_500
    description: str = "Something went wrong"

    def __init__(self, status=None, description=None):
        super().__init__(
            status=status or self.status,
            description=description or self.description,
        )

    def to_dict(self):
        return {
            "status": self.status,
            "description": self.description,
        }


class NotFoundError(BaseError):
    status = status_codes.HTTP_404
    description = "Not Found"


class AccessDenied(BaseError):
    status = status_codes.HTTP_403
    description = "Access denied"


class ValidationError(BaseError):
    status = status_codes.HTTP_400
    description = "Invalid request"


class InvalidSessionError(BaseError):
    status = status_codes.HTTP_401
    description = "Invalid session"


class ConflictError(BaseError):
    status = status_codes.HTTP_409
    description = "Duplicate resource"
