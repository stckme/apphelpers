from falcon import status_codes as codes


class BaseError(Exception):

    # Whether to report this error to honeybadger
    report = True

    code = codes.HTTP_500
    description: str = "Something went wrong"

    def __init__(self, code=None, description=None):
        self.code = code or self.__class__.code
        self.description = description or self.__class__.description

    def to_dict(self):
        return {
            "code": self.code,
            "description": self.description,
        }


class NotFoundError(BaseError):
    code = codes.HTTP_404


class AccessDenied(BaseError):
    code = codes.HTTP_403
    description = "Access denied"


class ValidationError(BaseError):
    code = codes.HTTP_400
    description = "Invalid request"


class InvalidSessionError(BaseError):
    code = codes.HTTP_401
    description = "Invalid session"


class ConflictError(BaseError):
    code = codes.HTTP_409
    description = "Duplicate resource"
