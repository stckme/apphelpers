from falcon import status_codes


class BaseError(Exception):

    # Whether to report this error to honeybadger
    report = True

    status = status_codes.HTTP_500
    description: str = "Something went wrong"

    def __init__(self, status=None, description=None):
        self.status = status or self.__class__.status
        self.description = description or self.__class__.description

    def to_dict(self):
        return {
            "status": self.status,
            "description": self.description,
        }


class NotFoundError(BaseError):
    status = status_codes.HTTP_404


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
