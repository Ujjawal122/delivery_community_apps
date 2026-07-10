"""
app/core/handlers.py
Global exception handlers registered on the FastAPI app.
"""

import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.responses import _body

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers."""

   
    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:

        logger.warning(
            "Application error",
            extra={
                "event": "app_error",
                "error_type": type(exc).__name__,
                "status_code": exc.status_code,
                "detail": exc.message,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=_body(
                False,
                exc.message,
                exc.detail,
            ),
        )

   
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:

        detail = (
            exc.detail
            if isinstance(exc.detail, str)
            else str(exc.detail)
        )

        logger.warning(
            "HTTP exception",
            extra={
                "event": "http_exception",
                "status_code": exc.status_code,
                "detail": detail,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=_body(
                False,
                detail,
                None,
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:

        errors = []

        for err in exc.errors():
            field = ".".join(
                str(loc)
                for loc in err["loc"]
                if loc != "body"
            )

            errors.append(
                {
                    "field": field or "request",
                    "message": err["msg"],
                }
            )

        logger.info(
            "Validation error",
            extra={
                "event": "validation_error",
                "path": request.url.path,
                "method": request.method,
                "errors": errors,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_body(
                False,
                "Validation failed",
                errors,
            ),
        )

 
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:

        logger.exception(
            "Unhandled exception",
            extra={
                "event": "internal_server_error",
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_body(
                False,
                "Internal server error",
                None,
            ),
        )