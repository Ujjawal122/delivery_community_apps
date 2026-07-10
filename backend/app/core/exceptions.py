

from typing import Any


# ── Base ───────────────────────────────────────────────────────────

class AppError(Exception):
   
    status_code: int = 500
    default_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        detail: Any = None,
    ) -> None:
        self.message = message or self.default_message
        self.detail = detail  # extra structured data (dict / list / None)
        super().__init__(self.message)




class BadRequestError(AppError):
    status_code = 400
    default_message = "Bad request"




class UnauthorizedError(AppError):
    status_code = 401
    default_message = "Authentication required"




class ForbiddenError(AppError):
    status_code = 403
    default_message = "You do not have permission to perform this action"



class NotFoundError(AppError):
    status_code = 404
    default_message = "Resource not found"



class ConflictError(AppError):
    status_code = 409
    default_message = "Resource already exists"




class PayloadTooLargeError(AppError):
    status_code = 413
    default_message = "Payload too large"




class UnprocessableError(AppError):
    status_code = 422
    default_message = "Unprocessable entity"



class ExternalServiceError(AppError):
    status_code = 502
    default_message = "External service error"
