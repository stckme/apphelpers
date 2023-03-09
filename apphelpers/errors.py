class BaseError(Exception):

    # Whether to report this error to honeybadger
    report = True

    code = 500
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
    code = 404


class AccessDenied(BaseError):
    code = 403
    description = "Access denied"


class ValidationError(BaseError):
    code = 400
    description = "Invalid request"


class InvalidSessionError(BaseError):
    code = 401
    description = "Invalid session"


class ConflictError(BaseError):
    code = 409
    description = "Duplicate resource"
