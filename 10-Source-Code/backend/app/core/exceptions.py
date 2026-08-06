from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code = 400
    error_code = "APP_ERROR"

    def __init__(self, message: str, details: list[dict] | None = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


class ValidationAppError(AppException):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppException):
    status_code = 409
    error_code = "CONFLICT"


class UnauthorizedError(AppException):
    status_code = 401
    error_code = "UNAUTHENTICATED"


class ForbiddenError(AppException):
    status_code = 403
    error_code = "FORBIDDEN"


class BusinessRuleError(AppException):
    status_code = 422
    error_code = "BUSINESS_RULE_VIOLATION"


def _error_envelope(exc: AppException) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"code": exc.error_code, "message": exc.message, "details": exc.details},
    }


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_error_envelope(exc))


def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
